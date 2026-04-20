"""
Main training loop for Vertical Federated Learning (VFL) with Split Learning.

Flow:
1. Client receives half_B image → computes embedding → sends to Server
2. Server receives embedding + processes half_A → concatenates → computes loss
3. Server backprops → computes gradient for Client → sends gradient
4. Client receives gradient → backprops through its model → updates weights
"""

import torch
import torch.nn.functional as F
from dataset import get_dataloaders
from client_bao import ClientWorker
from server_chien import ServerCoordinator


def calculate_accuracy(logits, labels):
    """Calculate accuracy"""
    _, predicted = torch.max(logits.data, 1)
    total = labels.size(0)
    correct = (predicted == labels).sum().item()
    return correct / total


def train_epoch(epoch, client, server, train_loader, device):
    """
    Train one epoch with Split Learning
    
    Args:
        epoch: Current epoch number
        client: ClientWorker instance
        server: ServerCoordinator instance
        train_loader: DataLoader for training
        device: 'cpu' or 'cuda'
    """
    client.train_mode()
    server.train_mode()
    
    total_loss = 0.0
    total_accuracy = 0.0
    num_batches = 0
    
    for batch_idx, (half_A, half_B, labels) in enumerate(train_loader):
        # Move data to device
        half_A = half_A.to(device)
        half_B = half_B.to(device)
        labels = labels.to(device)
        
        # ==========================================
        # Step 1: Client Forward
        # ==========================================
        o_client = client.forward(half_B)

        
        # ==========================================
        # Step 2: Server Forward and Loss
        # ==========================================
        loss, logits = server.forward_and_loss(half_A, o_client, labels)
        
        # ==========================================
        # Step 3: Server Backward - Compute Gradient for Client
        # ==========================================
        g_client = server.compute_gradients_and_update()
        
        # ==========================================
        # Step 4: Client Backward - Update Client Weights
        # ==========================================
        # Simulate receiving gradient from server
        # Client performs backward pass
        client.backward(g_client)
        
        # Compute metrics
        accuracy = calculate_accuracy(logits, labels)
        loss_value = loss.item()
        
        total_loss += loss_value
        total_accuracy += accuracy
        num_batches += 1
        
        # Print progress
        if (batch_idx + 1) % 100 == 0:
            print(f"  [{batch_idx + 1}/{len(train_loader)}] "
                  f"Loss: {loss_value:.4f}, Accuracy: {accuracy:.4f}")
    
    avg_loss = total_loss / num_batches
    avg_accuracy = total_accuracy / num_batches
    
    print(f"\n[Epoch {epoch}] Train Loss: {avg_loss:.4f}, Train Accuracy: {avg_accuracy:.4f}\n")
    
    return avg_loss, avg_accuracy


@torch.no_grad()
def test_epoch(epoch, client, server, test_loader, device):
    """
    Test/Evaluate one epoch
    
    Args:
        epoch: Current epoch number
        client: ClientWorker instance
        server: ServerCoordinator instance
        test_loader: DataLoader for testing
        device: 'cpu' or 'cuda'
    """
    client.eval_mode()
    server.eval_mode()
    
    total_loss = 0.0
    total_accuracy = 0.0
    num_batches = 0
    
    for half_A, half_B, labels in test_loader:
        # Move data to device
        half_A = half_A.to(device)
        half_B = half_B.to(device)
        labels = labels.to(device)
        
        # Client forward
        o_client = client.forward(half_B)
        
        # Server forward
        loss, logits = server.forward_and_loss(half_A, o_client, labels)
        
        # Compute metrics
        accuracy = calculate_accuracy(logits, labels)
        loss_value = loss.item()
        
        total_loss += loss_value
        total_accuracy += accuracy
        num_batches += 1
    
    avg_loss = total_loss / num_batches
    avg_accuracy = total_accuracy / num_batches
    
    print(f"[Epoch {epoch}] Test Loss: {avg_loss:.4f}, Test Accuracy: {avg_accuracy:.4f}\n")
    
    return avg_loss, avg_accuracy


def main():
    """
    Main training loop
    """
    # ==========================================
    # Configuration
    # ==========================================
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    BATCH_SIZE = 32
    LEARNING_RATE = 0.01
    NUM_EPOCHS = 10
    EMBEDDING_DIM = 128
    
    print("=" * 70)
    print("VERTICAL FEDERATED LEARNING (VFL) - BASE IMPLEMENTATION")
    print("=" * 70)
    print(f"Device: {DEVICE}")
    print(f"Batch Size: {BATCH_SIZE}")
    print(f"Learning Rate: {LEARNING_RATE}")
    print(f"Number of Epochs: {NUM_EPOCHS}")
    print(f"Embedding Dimension: {EMBEDDING_DIM}")
    print("=" * 70 + "\n")
    
    # ==========================================
    # Load Data
    # ==========================================
    print("[Main] Loading datasets...")
    train_loader, test_loader = get_dataloaders(batch_size=BATCH_SIZE)
    print(f"[Main] Train batches: {len(train_loader)}, Test batches: {len(test_loader)}\n")
    
    # ==========================================
    # Initialize Client and Server
    # ==========================================
    print("[Main] Initializing Client (Bảo)...")
    client = ClientWorker(
        embedding_dim=EMBEDDING_DIM,
        learning_rate=LEARNING_RATE,
        device=DEVICE
    )
    
    print("[Main] Initializing Server (Chiến)...")
    server = ServerCoordinator(
        embedding_dim=EMBEDDING_DIM,
        num_classes=10,
        learning_rate=LEARNING_RATE,
        device=DEVICE
    )
    
    print(f"[Main] Client parameters: {client.get_model_params()}")
    print(f"[Main] Server parameters: {server.get_model_params()}\n")
    
    # ==========================================
    # Training Loop
    # ==========================================
    print("=" * 70)
    print("STARTING TRAINING")
    print("=" * 70 + "\n")
    
    train_losses = []
    train_accuracies = []
    test_losses = []
    test_accuracies = []
    
    for epoch in range(1, NUM_EPOCHS + 1):
        print(f"\n{'=' * 70}")
        print(f"Epoch {epoch}/{NUM_EPOCHS}")
        print(f"{'=' * 70}")
        
        # Train
        train_loss, train_acc = train_epoch(epoch, client, server, train_loader, DEVICE)
        train_losses.append(train_loss)
        train_accuracies.append(train_acc)
        
        # Test
        test_loss, test_acc = test_epoch(epoch, client, server, test_loader, DEVICE)
        test_losses.append(test_loss)
        test_accuracies.append(test_acc)
    
    # ==========================================
    # Summary
    # ==========================================
    print("\n" + "=" * 70)
    print("TRAINING SUMMARY")
    print("=" * 70)
    print(f"Final Train Loss: {train_losses[-1]:.4f}")
    print(f"Final Train Accuracy: {train_accuracies[-1]:.4f}")
    print(f"Final Test Loss: {test_losses[-1]:.4f}")
    print(f"Final Test Accuracy: {test_accuracies[-1]:.4f}")
    print(f"Loss Reduction: {train_losses[0] - train_losses[-1]:.4f}")
    print(f"Accuracy Improvement: {train_accuracies[-1] - train_accuracies[0]:.4f}")
    print("=" * 70)
    
    print("\n✅ VFL Base System Training Complete!")
    print("   - Loss decreased from {:.4f} to {:.4f}".format(train_losses[0], train_losses[-1]))
    print("   - Accuracy increased from {:.4f} to {:.4f}".format(train_accuracies[0], train_accuracies[-1]))
    print("\n🎉 GIAI ĐOẠN 1 HOÀN THÀNH!")
    print("   Hãy báo cho tui để nhận PROMPT GIAI ĐOẠN 2 (Malicious Optimizer)!")


if __name__ == "__main__":
    main()
