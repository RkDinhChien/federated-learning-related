"""
Client module for Vertical Federated Learning (VFL).
The Client (Passive Participant) receives half_B of images and sends embeddings to Server.
Does NOT have access to labels.

⚠️ CRITICAL: Computation graph must be preserved throughout forward/backward cycle
to ensure gradients flow correctly and weights are updated properly.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torchvision.models import resnet18


class BottomModel(nn.Module):
    """
    Bottom Model for Client (Passive Participant).
    - Input: Half-image (3 × 32 × 16)
    - Output: Feature embedding vector
    - Modified ResNet-18 with adjusted first conv layer to accept 3×32×16 input
    """
    
    def __init__(self, embedding_dim=128):
        """
        Args:
            embedding_dim: Dimension of output feature vector
        """
        super(BottomModel, self).__init__()
        self.embedding_dim = embedding_dim
        
        # Load pretrained ResNet-18
        resnet = resnet18(pretrained=True)
        
        # CRITICAL FIX: Modify first conv layer to accept 3 × 32 × 16 input
        # Original ResNet-18 conv1: Conv2d(3, 64, kernel_size=7, stride=2, padding=3)
        # Problem: stride=2 with width=16 causes dimension issues
        # Solution: kernel_size=3, stride=1, padding=1 preserves spatial dimensions
        self.conv1 = nn.Conv2d(in_channels=3, out_channels=64, kernel_size=3, stride=1, padding=1)
        self.bn1 = resnet.bn1
        self.relu = resnet.relu
        self.maxpool = resnet.maxpool
        
        # Keep ResNet residual blocks
        self.layer1 = resnet.layer1
        self.layer2 = resnet.layer2
        self.layer3 = resnet.layer3
        self.layer4 = resnet.layer4
        self.avgpool = resnet.avgpool
        
        # Projection layer: ResNet-18 layer4 output is 512-dim
        self.fc = nn.Linear(512, embedding_dim)
    
    def forward(self, x_client):
        """
        Forward pass for Client's half image.
        
        Args:
            x_client: Input tensor (batch_size, 3, 32, 16)
        
        Returns:
            embedding: Feature vector (batch_size, embedding_dim)
                       with computation graph intact for backprop
        """
        x = self.conv1(x_client)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        
        # ResNet residual blocks
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        
        # Global average pooling
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        
        # Projection to embedding space
        embedding = self.fc(x)
        
        return embedding


class ClientWorker:
    """
    Client Worker manages the Bottom Model for passive participant.
    
    Responsibilities:
    1. forward(half_B): Process client's image half through BottomModel
    2. backward(g_bao): Receive gradient from Server, update weights
    3. Maintain optimizer state and computation graph integrity
    
    ⚠️ KEY REQUIREMENTS:
    - NO torch.no_grad() in forward() to preserve computation graph
    - Store output in self.o_bao for backward pass
    - backward() uses: zero_grad() → backward(g_bao) → step()
    """
    
    def __init__(self, embedding_dim=128, learning_rate=0.001, momentum=0.9, device='cpu'):
        """
        Args:
            embedding_dim: Dimension of feature embeddings
            learning_rate: SGD learning rate (reduced to 0.001 to prevent NaN)
            momentum: SGD momentum for better convergence
            device: 'cpu' or 'cuda'
        """
        self.device = device
        self.embedding_dim = embedding_dim
        self.max_grad_norm = 1.0  # Gradient clipping threshold
        
        # Initialize Bottom Model
        self.model = BottomModel(embedding_dim=embedding_dim).to(device)
        
        # CRITICAL: SGD with momentum=0.9 and lower learning rate
        self.optimizer = optim.SGD(
            self.model.parameters(), 
            lr=learning_rate, 
            momentum=momentum
        )
        
        # Storage for computation graph (ESSENTIAL for backward pass)
        self.o_bao = None
        
        print(f"[ClientWorker] Initialized on device: {device}")
        print(f"[ClientWorker] Embedding dimension: {embedding_dim}")
        print(f"[ClientWorker] Optimizer: SGD(lr={learning_rate}, momentum={momentum})")
        print(f"[ClientWorker] Gradient clipping enabled: max_norm={self.max_grad_norm}")
    
    def forward(self, half_B):
        """
        Forward pass: Process half_B through BottomModel.
        
        ⚠️ CRITICAL: NO torch.no_grad() here - preserves computation graph when gradients enabled!
        
        Args:
            half_B: Input tensor (batch_size, 3, 32, 16) - Client's image portion
        
        Returns:
            self.o_bao: Feature embedding (batch_size, embedding_dim)
                        with computation graph preserved (when torch.is_grad_enabled())
        """
        # FIXED: Don't force train mode - respect current model state (train/eval)
        # The model state should be set externally via train_mode()/eval_mode()
        
        # Forward pass - computation graph is automatically tracked when gradients enabled
        self.o_bao = self.model(half_B)
        
        # FIXED: Only enforce requires_grad when gradients are actually enabled
        # During evaluation with @torch.no_grad(), this will be False and that's OK
        if torch.is_grad_enabled():
            assert self.o_bao.requires_grad, \
                "[ClientWorker] ERROR: Output must have requires_grad=True when gradients are enabled!"
        
        return self.o_bao
    
    def backward(self, g_bao):
        """
        Backward pass: Receive gradient from Server and update Client's weights.
        
        ⚠️ CRITICAL SEQUENCE (do NOT change order):
        1. optimizer.zero_grad() - clear old gradients
        2. self.o_bao.backward(g_bao) - backprop Server's gradient
        3. clip_grad_norm_ - prevent gradient explosion
        4. optimizer.step() - update weights
        
        Args:
            g_bao: Gradient of loss w.r.t. o_bao from Server
                   Shape: (batch_size, embedding_dim)
        """
        # Step 1: Clear gradients from previous iteration
        self.optimizer.zero_grad()
        
        # Step 2: CORE BACKPROP - propagate Server's gradient back through Client's model
        # This computes dL/dθ for all parameters θ in BottomModel
        self.o_bao.backward(g_bao)
        
        # Step 3: GRADIENT CLIPPING - prevent NaN and explosion
        # Clip gradients to prevent numerical instability
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.max_grad_norm)
        
        # Step 4: Update Client's model weights using SGD
        self.optimizer.step()
    
    def eval_mode(self):
        """Switch model to evaluation mode"""
        self.model.eval()
    
    def train_mode(self):
        """Switch model to training mode"""
        self.model.train()
    
    def get_model_params(self):
        """Get total number of trainable parameters"""
        return sum(p.numel() for p in self.model.parameters() if p.requires_grad)
