"""
Client module for Vertical Federated Learning (VFL).
The Client (Passive Participant) receives half_B of images and sends embeddings to Server.
Does NOT have access to labels.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torchvision.models import ResNet18_Weights, resnet18


class BottomModel(nn.Module):
    """
    Bottom Model for Client (Passive Participant).
    - Input: Half-image (3 × 32 × 16)
    - Output: Feature embedding vector
    - Modified ResNet-18 with adjusted first conv layer to accept 16-width input
    """
    
    def __init__(self, embedding_dim=128):
        """
        Args:
            embedding_dim: Dimension of output feature vector
        """
        super(BottomModel, self).__init__()
        self.embedding_dim = embedding_dim
        
        # Load weights ResNet-18
        resnet = resnet18(weights=ResNet18_Weights.DEFAULT)
        
        # Modify first conv layer to accept 3 × 32 × 16 input
        # Original: Conv2d(3, 64, kernel_size=7, stride=2, padding=3)
        # Problem: stride=2 and input width=16 would cause dimension issues
        # Solution: Use a custom first layer with kernel_size=3, stride=1, padding=1
        self.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1)
        self.bn1 = resnet.bn1
        self.relu = resnet.relu
        self.maxpool = resnet.maxpool
        
        # Keep ResNet blocks
        self.layer1 = resnet.layer1
        self.layer2 = resnet.layer2
        self.layer3 = resnet.layer3
        self.layer4 = resnet.layer4
        self.avgpool = resnet.avgpool
        
        # Original ResNet output is 512-dim (from layer4)
        # Project to embedding_dim
        self.fc = nn.Linear(512, embedding_dim)
    
    def forward(self, x_client):
        """
        Forward pass for Client's half image.
        
        Args:
            x_client: Input tensor (batch_size, 3, 32, 16)
        
        Returns:
            embedding: Feature vector (batch_size, embedding_dim)
        """
        # Conv block
        x = self.conv1(x_client)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        
        # ResNet layers
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        
        # Global average pooling
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        
        # Project to embedding dimension
        embedding = self.fc(x)
        
        # Keep gradient tracking for backprop
        embedding.requires_grad_(True)
        
        return embedding


class ClientWorker:
    """
    Client Worker manages the Bottom Model for passive participant.
    Responsibilities:
    1. Forward half_B through BottomModel to get embeddings
    2. Receive gradients from Server and perform backward pass
    3. Update its own weights using SGD
    """
    
    def __init__(self, embedding_dim=128, learning_rate=0.01, device='cpu'):
        """
        Args:
            embedding_dim: Dimension of feature embeddings
            learning_rate: SGD learning rate
            device: 'cpu' or 'cuda'
        """
        self.device = device
        self.embedding_dim = embedding_dim
        
        # Initialize Bottom Model
        self.model = BottomModel(embedding_dim=embedding_dim).to(device)
        
        # Optimizer for Client
        self.optimizer = optim.SGD(self.model.parameters(), lr=learning_rate)
        
        print(f"[ClientWorker] Initialized on {device}")
        print(f"[ClientWorker] Embedding dimension: {embedding_dim}")
    
    def forward(self, x_client):
        """
        Forward pass: Client receives half_B and computes embeddings.
        
        Args:
            x_client: Input tensor (batch_size, 3, 32, 16)
        
        Returns:
            o_client: Feature embedding (batch_size, embedding_dim)
                      with requires_grad=True for backward pass
        """
        self.model.train()
        x_client = x_client.to(self.device)
        o_client = self.model(x_client)
        
        # Ensure gradient tracking is enabled
        if not o_client.requires_grad:
            o_client.requires_grad_(True)

        self.current_embedding = o_client # Store current embedding for backward pass
        
        return o_client
    
    def backward(self, gradient_from_server):
        """
        Backward pass: Client receives gradient from Server and updates weights.
        
        Args:
            gradient_from_server: Gradient of loss w.r.t. o_client (from Server)
                                  Shape: (batch_size, embedding_dim)
        """
        # Set the gradient of embeddings from Server's backward pass
        # We need to backprop through the embedding to update Client's weights
        gradient_from_server = gradient_from_server.to(self.device)
        # Zero gradients
        self.optimizer.zero_grad()
        
        # Use a surrogate loss: L = sum(o_client * gradient_from_server)
        # This effectively backprops the Server's gradient through Client's model
        surrogate_loss = (self.current_embedding * gradient_from_server).sum()
        surrogate_loss.backward()
        
        # Update Client weights
        self.optimizer.step()
        
        #print(f"[ClientWorker] Backward pass completed, weights updated")
    
    def set_current_embedding(self, embedding):
        """Store current embedding for backward pass"""
        self.current_embedding = embedding
    
    def eval_mode(self):
        """Switch to evaluation mode"""
        self.model.eval()
    
    def train_mode(self):
        """Switch to training mode"""
        self.model.train()
    
    def get_model_params(self):
        """Get model parameters for monitoring"""
        return sum(p.numel() for p in self.model.parameters() if p.requires_grad)


if __name__ == "__main__":
    # Test ClientWorker
    print("[Test] Creating ClientWorker...")
    client = ClientWorker(embedding_dim=128, learning_rate=0.01)
    
    # Dummy input: batch_size=4, 3 channels, 32 height, 16 width
    x_dummy = torch.randn(4, 3, 32, 16)
    
    print("[Test] Forward pass with dummy input...")
    embedding = client.forward(x_dummy)
    print(f"  Embedding shape: {embedding.shape}")
    print(f"  Embedding requires_grad: {embedding.requires_grad}")
    
    print("[Test] Total parameters in ClientWorker: ", client.get_model_params())
