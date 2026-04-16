"""
Server module for Vertical Federated Learning (VFL).
The Server (Active Participant) has access to labels, computes loss, 
and orchestrates training with the Client.
"""

import torch
import torch.nn as nn
import torch.optim as optim


class BottomModelServer(nn.Module):
    """
    Bottom Model for Server's portion of the image.
    Processes half_A (3 × 32 × 16) to extract features.
    Architecture: Similar to Client but smaller/simpler.
    """
    
    def __init__(self, embedding_dim=128):
        """
        Args:
            embedding_dim: Dimension of output feature vector
        """
        super(BottomModelServer, self).__init__()
        self.embedding_dim = embedding_dim
        
        # Simple CNN for Server's half image
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            
            nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
        )
        
        # After pooling (2x2 twice): 32 → 16 → 8, so spatial size: 8x8
        # Channels: 64, so flattened: 64 * 8 * 8 = 4096
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        
        # Project to embedding_dim
        self.fc = nn.Linear(64, embedding_dim)
    
    def forward(self, x_server):
        """
        Forward pass for Server's half image.
        
        Args:
            x_server: Input tensor (batch_size, 3, 32, 16)
        
        Returns:
            embedding: Feature vector (batch_size, embedding_dim)
        """
        x = self.features(x_server)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        embedding = self.fc(x)
        
        return embedding


class TopModel(nn.Module):
    """
    Top Model for Server (Active Participant).
    - Receives concatenated embeddings from Client and Server
    - Outputs logits for 10 classes (CIFAR-10)
    - Architecture: Fully Connected Neural Network with 4 layers (FCNN-4)
    """
    
    def __init__(self, embedding_dim=128, num_classes=10, hidden_dim=256):
        """
        Args:
            embedding_dim: Dimension of each input embedding (Client + Server)
            num_classes: Number of output classes (10 for CIFAR-10)
            hidden_dim: Hidden layer dimension
        """
        super(TopModel, self).__init__()
        
        # Input: concatenated embedding (2 * embedding_dim)
        self.fc_layers = nn.Sequential(
            nn.Linear(2 * embedding_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            
            nn.Linear(hidden_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.BatchNorm1d(hidden_dim // 2),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            
            nn.Linear(hidden_dim // 2, num_classes)
        )
    
    def forward(self, o_concatenated):
        """
        Forward pass for Top Model.
        
        Args:
            o_concatenated: Concatenated embedding (batch_size, 2 * embedding_dim)
        
        Returns:
            logits: Classification logits (batch_size, num_classes)
        """
        logits = self.fc_layers(o_concatenated)
        return logits


class ServerCoordinator:
    """
    Server Coordinator manages the training process.
    Responsibilities:
    1. Maintain Server's Bottom Model and Top Model
    2. Receive embeddings from Client
    3. Compute forward pass and loss
    4. Compute gradients and send gradient to Client
    5. Update own weights
    """
    
    def __init__(self, embedding_dim=128, num_classes=10, learning_rate=0.01, device='cpu'):
        """
        Args:
            embedding_dim: Dimension of feature embeddings
            num_classes: Number of output classes
            learning_rate: SGD learning rate
            device: 'cpu' or 'cuda'
        """
        self.device = device
        self.embedding_dim = embedding_dim
        self.num_classes = num_classes
        
        # Server's Bottom Model (for Server's half image)
        self.bottom_model = BottomModelServer(embedding_dim=embedding_dim).to(device)
        
        # Server's Top Model (for final classification)
        self.top_model = TopModel(embedding_dim=embedding_dim, num_classes=num_classes).to(device)
        
        # Loss function
        self.criterion = nn.CrossEntropyLoss()
        
        # Optimizer for Server (combines both models' parameters)
        all_params = list(self.bottom_model.parameters()) + list(self.top_model.parameters())
        self.optimizer = optim.SGD(all_params, lr=learning_rate)
        
        # Store current embeddings for gradient computation
        self.o_server = None
        self.o_client = None
        self.logits = None
        self.loss = None
        
        print(f"[ServerCoordinator] Initialized on {device}")
        print(f"[ServerCoordinator] Embedding dimension: {embedding_dim}")
    
    def forward_and_loss(self, x_server, o_client, labels):
        """
        Forward pass and loss computation.
        
        Args:
            x_server: Server's half image (batch_size, 3, 32, 16)
            o_client: Client's embedding from Client.forward() (batch_size, embedding_dim)
            labels: Ground truth labels (batch_size,)
        
        Returns:
            loss: Cross-entropy loss value
            logits: Output logits for monitoring
        """
        self.bottom_model.train()
        self.top_model.train()

        x_server = x_server.to(self.device)
        o_client = o_client.to(self.device)
        labels = labels.to(self.device)
        
        # Server computes its own embedding
        self.o_server = self.bottom_model(x_server)
        
        # Store client embedding
        self.o_client = o_client.detach()  # Detach from client graph
        self.o_client.requires_grad_(True)  # But enable grad for backward
        
        # Concatenate embeddings
        o_concatenated = torch.cat([self.o_server, self.o_client], dim=1)
        
        # Forward through Top Model
        self.logits = self.top_model(o_concatenated)
        
        # Compute loss
        self.loss = self.criterion(self.logits, labels)
        
        return self.loss, self.logits
    
    def compute_gradients_and_update(self):
        """
        Compute gradients, update Server's weights, and return gradient for Client.
        
        Returns:
            g_client: Gradient of loss w.r.t. o_client (to send to Client)
                      Shape: (batch_size, embedding_dim)
        """
        # Zero gradients
        self.optimizer.zero_grad()
        
        # Backward pass
        self.loss.backward()
        
        # Extract gradient w.r.t. client embedding
        g_client = self.o_client.grad.clone()
        
        # Update Server's weights
        self.optimizer.step()
        
        return g_client
    
    def eval_mode(self):
        """Switch to evaluation mode"""
        self.bottom_model.eval()
        self.top_model.eval()
    
    def train_mode(self):
        """Switch to training mode"""
        self.bottom_model.train()
        self.top_model.train()
    
    def get_model_params(self):
        """Get total model parameters"""
        params = sum(p.numel() for p in self.bottom_model.parameters())
        params += sum(p.numel() for p in self.top_model.parameters())
        return params
    
    def get_last_logits(self):
        """Get last computed logits"""
        return self.logits
    
    def get_last_loss(self):
        """Get last computed loss"""
        return self.loss.item() if self.loss is not None else None


if __name__ == "__main__":
    # Test ServerCoordinator
    print("[Test] Creating ServerCoordinator...")
    server = ServerCoordinator(embedding_dim=128, num_classes=10)
    
    # Dummy inputs
    x_server = torch.randn(4, 3, 32, 16)
    o_client = torch.randn(4, 128)
    labels = torch.randint(0, 10, (4,))
    
    print("[Test] Forward pass with dummy inputs...")
    loss, logits = server.forward_and_loss(x_server, o_client, labels)
    print(f"  Loss: {loss.item():.4f}")
    print(f"  Logits shape: {logits.shape}")
    
    print("[Test] Computing gradients and updating...")
    g_client = server.compute_gradients_and_update()
    print(f"  Gradient for Client shape: {g_client.shape}")
    
    print("[Test] Total parameters in ServerCoordinator: ", server.get_model_params())
