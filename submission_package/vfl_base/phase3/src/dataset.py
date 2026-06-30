"""
Dataset module for Vertical Federated Learning (VFL) with CIFAR-10.
Splits images vertically into two halves:
- Half A (3 × 32 × 16): For Server
- Half B (3 × 32 × 16): For Client (passive participant)
"""

import torch
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import Dataset, DataLoader


class VFLCIFARDataset(Dataset):
    """
    Custom Dataset for VFL that loads CIFAR-10 and splits images vertically.
    Returns:
        - half_A: Image slice for Server (3 × 32 × 16)
        - half_B: Image slice for Client (3 × 32 × 16)
        - label: Ground truth label (only used by Server)
    """
    
    def __init__(self, dataset):
        """
        Args:
            dataset: CIFAR-10 dataset from torchvision
        """
        self.dataset = dataset
    
    def __len__(self):
        return len(self.dataset)
    
    def __getitem__(self, idx):
        image, label = self.dataset[idx]
        
        # image shape: (3, 32, 32)
        # Split vertically into two halves along width dimension
        half_A = image[:, :, :16]   # (3, 32, 16) - Server's portion
        half_B = image[:, :, 16:]   # (3, 32, 16) - Client's portion
        
        return half_A, half_B, label


def get_dataloaders(batch_size=32, num_workers=2):
    """
    Load CIFAR-10 train and test datasets with vertical partitioning.
    
    Args:
        batch_size: Batch size for DataLoader
        num_workers: Number of workers for data loading
    
    Returns:
        train_loader: DataLoader for training set
        test_loader: DataLoader for test set
    """
    # Define transforms for CIFAR-10
    transform_train = transforms.Compose([
        transforms.RandomHorizontalFlip(),
        transforms.RandomCrop(32, padding=4),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=(0.4914, 0.4822, 0.4465),
            std=(0.2023, 0.1994, 0.2010)
        )
    ])
    
    transform_test = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(
            mean=(0.4914, 0.4822, 0.4465),
            std=(0.2023, 0.1994, 0.2010)
        )
    ])
    
    # Download and load CIFAR-10
    print("[Dataset] Loading CIFAR-10 train set...")
    cifar_train = torchvision.datasets.CIFAR10(
        root='./data', 
        train=True, 
        download=True, 
        transform=transform_train
    )
    
    print("[Dataset] Loading CIFAR-10 test set...")
    cifar_test = torchvision.datasets.CIFAR10(
        root='./data', 
        train=False, 
        download=True, 
        transform=transform_test
    )
    
    # Wrap with VFL dataset
    vfl_train = VFLCIFARDataset(cifar_train)
    vfl_test = VFLCIFARDataset(cifar_test)
    
    # Create dataloaders
    train_loader = DataLoader(
        vfl_train, 
        batch_size=batch_size, 
        shuffle=True, 
        num_workers=num_workers,
        pin_memory=True
    )
    
    test_loader = DataLoader(
        vfl_test, 
        batch_size=batch_size, 
        shuffle=False, 
        num_workers=num_workers,
        pin_memory=True
    )
    
    print(f"[Dataset] Train samples: {len(vfl_train)}, Test samples: {len(vfl_test)}")
    print(f"[Dataset] Each image split: Server gets (3, 32, 16), Client gets (3, 32, 16)")
    
    return train_loader, test_loader
