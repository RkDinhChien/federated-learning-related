"""
Server module for Vertical Federated Learning (VFL) with integrated FLSG Defense.
Server (Active Participant) coordinates training with defense against MaliciousSGD attacks.

Architecture:
- BottomModelServer: Processes Server's image half (3 × 32 × 16)
- TopModel: Combines embeddings from Server + Client, produces predictions
- Defense: GradientDefenseModule intercepts and defends client gradients

Key modifications from Phase 1:
- Added enable_defense parameter for defense mechanism
- Added defense_config for customization
- Integrated gradient defense in compute_gradients_and_update()
"""

import torch
import torch.nn as nn
import torch.optim as optim
from gradient_defense import GradientDefenseModule, DefenseConfig
from flsg_defender import FLSG_Defender


class BottomModelServer(nn.Module):
    """
    Bottom Model for Server (Active Participant).
    - Input: Half-image (3 × 32 × 16)
    - Output: Feature embedding vector (128-dim)
    """
    
    def __init__(self, embedding_dim=128):
        super(BottomModelServer, self).__init__()
        self.embedding_dim = embedding_dim
        
        # Simple CNN for Server's bottom model
        self.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1)
        self.bn1 = nn.BatchNorm2d(64)
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)
        
        self.conv2 = nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm2d(128)
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)
        
        self.conv3 = nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1)
        self.bn3 = nn.BatchNorm2d(256)
        self.pool3 = nn.AdaptiveAvgPool2d((1, 1))
        
        # Projection to embedding
        self.fc = nn.Linear(256, embedding_dim)
    
    def forward(self, x_server):
        """
        Args:
            x_server: (batch_size, 3, 32, 16)
        Returns:
            embedding: (batch_size, 128)
        """
        x = torch.relu(self.bn1(self.conv1(x_server)))
        x = self.pool1(x)
        
        x = torch.relu(self.bn2(self.conv2(x)))
        x = self.pool2(x)
        
        x = torch.relu(self.bn3(self.conv3(x)))
        x = self.pool3(x)
        x = torch.flatten(x, 1)
        
        embedding = self.fc(x)
        return embedding


class TopModel(nn.Module):
    """
    Top Model processes combined embeddings from Server + Client.
    - Input: Concatenated embeddings (256-dim: 128 from Server + 128 from Client)
    - Output: Class logits (10 for CIFAR-10)
    """
    
    def __init__(self, embedding_dim=128, num_classes=10):
        super(TopModel, self).__init__()
        self.embedding_dim = embedding_dim
        
        # Fully connected layers after concatenation
        self.fc1 = nn.Linear(embedding_dim * 2, 256)
        self.bn1 = nn.BatchNorm1d(256)
        self.dropout1 = nn.Dropout(0.5)
        
        self.fc2 = nn.Linear(256, 256)
        self.bn2 = nn.BatchNorm1d(256)
        self.dropout2 = nn.Dropout(0.5)
        
        self.fc3 = nn.Linear(256, 128)
        self.bn3 = nn.BatchNorm1d(128)
        self.dropout3 = nn.Dropout(0.3)
        
        self.fc4 = nn.Linear(128, num_classes)
    
    def forward(self, combined_embedding):
        """
        Args:
            combined_embedding: (batch_size, 256) = concat(server_emb, client_emb)
        Returns:
            logits: (batch_size, 10)
        """
        x = torch.relu(self.bn1(self.fc1(combined_embedding)))
        x = self.dropout1(x)
        
        x = torch.relu(self.bn2(self.fc2(x)))
        x = self.dropout2(x)
        
        x = torch.relu(self.bn3(self.fc3(x)))
        x = self.dropout3(x)
        
        logits = self.fc4(x)
        return logits


class ServerCoordinator:
    """
    Server Coordinator manages the training process with optional defense.
    
    Responsibilities:
    1. forward(half_A, o_bao): Process Server's half + Client embedding
    2. compute_gradients_and_update(loss): Backward pass with optional defense
    3. Defense integration: Apply GradientDefenseModule to client gradients
    
    NEW: Defense mechanism support
    - enable_defense: Toggle defense mechanism on/off
    - defense_config: Configuration for GradientDefenseModule
    - defense_module: Active defense instance when enabled
    """
    
    def __init__(self, embedding_dim=128, learning_rate=0.001, device='cpu',
                 enable_defense=False, defense_config=None):
        """
        Args:
            embedding_dim: Dimension of feature embeddings
            learning_rate: SGD learning rate
            device: 'cpu' or 'cuda'
            enable_defense: Enable FLSG defense mechanism (NEW)
            defense_config: DefenseConfig instance for defense parameters (NEW)
        """
        self.device = device
        self.embedding_dim = embedding_dim
        self.enable_defense = enable_defense
        self.defense_config = defense_config
        
        # Initialize models
        self.bottom_model = BottomModelServer(embedding_dim=embedding_dim).to(device)
        self.top_model = TopModel(embedding_dim=embedding_dim, num_classes=10).to(device)
        
        # Optimizer for Server's models
        self.optimizer = optim.SGD(
            list(self.bottom_model.parameters()) + list(self.top_model.parameters()),
            lr=learning_rate,
            momentum=0.9
        )
        
        # Loss function
        self.criterion = nn.CrossEntropyLoss()
        
        # Defense module (NEW)
        if self.enable_defense:
            if defense_config is None:
                defense_config = DefenseConfig()
            self.defense_module = GradientDefenseModule(defense_config, device=device)
            self.flsg_defender = FLSG_Defender(device=device)
            print(f"[ServerCoordinator] Defense enabled with config: {defense_config}")
        else:
            self.defense_module = None
            self.flsg_defender = None
            print("[ServerCoordinator] Defense DISABLED")
        
        # Storage for computation graph
        self.o_bao = None
        self.o_server = None
        self.logits = None
        
        print(f"[ServerCoordinator] Initialized on device: {device}")
        print(f"[ServerCoordinator] Embedding dimension: {embedding_dim}")
    
    def forward(self, half_A, o_bao):
        """
        Forward pass: Process Server's half and Client embedding.
        
        Args:
            half_A: Server's image portion (batch_size, 3, 32, 16)
            o_bao: Client's embedding from forward pass (batch_size, 128)
        
        Returns:
            logits: Network predictions (batch_size, 10)
        """
        # Process Server's half
        self.o_server = self.bottom_model(half_A)
        
        # Store Client's embedding
        self.o_bao = o_bao
        # CRITICAL: Retain gradient for non-leaf tensor (will be concatenated)
        if self.o_bao.requires_grad:
            self.o_bao.retain_grad()
        
        # Concatenate embeddings
        combined = torch.cat([self.o_server, self.o_bao], dim=1)
        
        # Top model processes combined embedding
        self.logits = self.top_model(combined)
        
        return self.logits
    
    def compute_gradients_and_update(self, loss, return_client_gradient=True):
        """
        Backward pass with optional defense mechanism.
        
        ⚠️ CRITICAL SEQUENCE:
        1. optimizer.zero_grad() - clear old gradients
        2. loss.backward() - compute all gradients
        3. DEFENSE: Apply defense to client gradient if enabled (NEW)
        4. optimizer.step() - update Server's weights
        5. Return modified gradient to Client
        
        Args:
            loss: Scalar loss from TopModel
            return_client_gradient: Return gradient for Client backward (True during training)
        
        Returns:
            g_bao: Gradient of loss w.r.t. o_bao for Client backward
                   If defense_enabled: gradient is modified by GradientDefenseModule
        """
        # Step 1: Clear old gradients
        self.optimizer.zero_grad()
        
        # Step 2: Compute gradients via backprop
        # Use retain_graph=True because we'll call backward twice:
        # - Once here for loss.backward()
        # - Once in client.backward(g_bao)
        loss.backward(retain_graph=True)
        
        # Step 3: DEFENSE (NEW) - Apply FLSG defense to client gradient
        # Extract gradient w.r.t. client embedding before step
        if self.enable_defense and self.o_bao.grad is not None:
            # Apply FLSG defense to obfuscate gradient
            g_obfuscated = self.flsg_defender.apply_defense(
                self.o_bao.grad,
                tau=0.1,  # Cosine distance threshold
                R=1000    # Number of fake gradients
            )
            # Replace gradient with obfuscated version
            self.o_bao.grad = g_obfuscated
        
        # Step 4: Update Server's weights
        torch.nn.utils.clip_grad_norm_(
            list(self.bottom_model.parameters()) + list(self.top_model.parameters()),
            max_norm=1.0
        )
        self.optimizer.step()
        
        # Step 5: Return gradient for Client backward
        if return_client_gradient:
            g_bao = self.o_bao.grad.clone().detach()
            return g_bao
        else:
            return None
    
    def eval_mode(self):
        """Switch to evaluation mode"""
        self.bottom_model.eval()
        self.top_model.eval()
    
    def train_mode(self):
        """Switch to training mode"""
        self.bottom_model.train()
        self.top_model.train()
    
    def get_defense_statistics(self):
        """
        Get defense statistics (NEW).
        
        Returns:
            dict: Defense statistics if enabled, None otherwise
        """
        if self.enable_defense and self.defense_module is not None:
            return self.defense_module.get_statistics()
        return None
    
    def get_defense_logs(self):
        """
        Get defense action logs (NEW).
        
        Returns:
            list: List of defense action logs if enabled, None otherwise
        """
        if self.enable_defense and self.defense_module is not None:
            return self.defense_module.logs
        return None
    
    def print_defense_statistics(self):
        """Print formatted defense statistics (NEW)"""
        if self.enable_defense and self.defense_module is not None:
            self.defense_module.print_statistics()
    
    def get_model_params(self):
        """Get total number of trainable parameters"""
        return (sum(p.numel() for p in self.bottom_model.parameters() if p.requires_grad) +
                sum(p.numel() for p in self.top_model.parameters() if p.requires_grad))
