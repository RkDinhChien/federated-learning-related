"""
FLSG Defender: Federated Learning Similar Gradients Defense
Based on IEEE IoT 2024 Paper
Vectorized implementation to prevent hanging
"""

import torch
import torch.nn.functional as F
from typing import Dict


class FLSG_Defender:
    """
    FLSG Defense mechanism to protect against Label Inference Attacks
    Uses gradient obfuscation with similar synthetic gradients
    """
    
    def __init__(self, device: str = 'cpu'):
        self.device = device
        self.defense_count = 0
    
    def apply_defense(self, 
                      g_real: torch.Tensor, 
                      tau: float = 0.1, 
                      R: int = 1000) -> torch.Tensor:
        """
        Apply FLSG defense to gradient
        
        Args:
            g_real: Original gradient tensor from server
            tau: Cosine Distance threshold (0 < tau <= 1)
            R: Number of fake gradient samples to generate
        
        Returns:
            g_fake: Obfuscated gradient (detached, no grad)
        """
        
        # Step 1: Store original shape and device
        original_shape = g_real.shape
        device = g_real.device
        
        # Flatten gradient to 1D vector
        v = g_real.clone().detach().view(-1).float()
        v_len = v.shape[0]
        
        # Step 2: Compute statistics
        mu = v.mean().item()  # Mean
        phi = v.std().item()  # Standard deviation
        v_max = v.max().item()
        v_min = v.min().item()
        
        # Handle edge case where std is 0
        if phi < 1e-8:
            phi = 1e-8
        
        # Step 3: VECTORIZED - Generate R fake gradients at once (batch)
        # Shape: (R, v_len)
        v_fake_batch = torch.normal(
            mean=mu,
            std=phi,
            size=(R, v_len),
            device=device,
            dtype=torch.float32
        )
        
        # Step 4: Clamp all fake gradients to [v_min, v_max]
        v_fake_batch = torch.clamp(v_fake_batch, min=v_min, max=v_max)
        
        # Step 5: VECTORIZED - Compute Cosine Distance for entire batch
        # Cosine Similarity = (A·B) / (||A|| * ||B||)
        # Cosine Distance = 1 - Cosine Similarity
        
        # Normalize vectors
        v_normalized = F.normalize(v.unsqueeze(0), p=2, dim=1)  # Shape: (1, v_len)
        v_fake_normalized = F.normalize(v_fake_batch, p=2, dim=1)  # Shape: (R, v_len)
        
        # Compute cosine similarity: (1, v_len) × (R, v_len)^T = (1, R)
        cosine_sim = torch.mm(v_normalized, v_fake_normalized.t())  # Shape: (1, R)
        cosine_sim = cosine_sim.squeeze(0)  # Shape: (R,)
        
        # Cosine Distance
        cosine_dist = 1.0 - cosine_sim  # Shape: (R,)
        
        # Step 6: Filter gradients with Cosine Distance <= tau
        mask = cosine_dist <= tau
        valid_indices = torch.where(mask)[0]
        
        if valid_indices.shape[0] > 0:
            # At least one valid gradient found
            # Randomly select one
            selected_idx = valid_indices[torch.randint(0, valid_indices.shape[0], (1,))].item()
            v_fake = v_fake_batch[selected_idx]
        else:
            # No valid gradient found - select one with minimum Cosine Distance
            min_idx = torch.argmin(cosine_dist).item()
            v_fake = v_fake_batch[min_idx]
        
        # Step 7: Reshape back to original shape
        g_fake = v_fake.view(original_shape)
        
        self.defense_count += 1
        
        # Return without gradient (detached)
        return g_fake.detach()
    
    def compute_defense_metrics(self, 
                               g_real: torch.Tensor,
                               g_fake: torch.Tensor) -> Dict:
        """
        Compute metrics for defense evaluation
        """
        v_real = g_real.view(-1).float()
        v_fake = g_fake.view(-1).float()
        
        # Cosine similarity
        cosine_sim = F.cosine_similarity(v_real.unsqueeze(0), v_fake.unsqueeze(0))
        cosine_dist = 1.0 - cosine_sim.item()
        
        # L2 distance
        l2_dist = torch.norm(v_real - v_fake).item()
        
        # Relative perturbation
        rel_perturb = l2_dist / (torch.norm(v_real).item() + 1e-8)
        
        return {
            'cosine_distance': cosine_dist,
            'l2_distance': l2_dist,
            'relative_perturbation': rel_perturb,
        }
