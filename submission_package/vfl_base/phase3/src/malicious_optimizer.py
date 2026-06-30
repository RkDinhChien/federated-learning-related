import torch
import torch.optim as optim
import torch.nn as nn

class MaliciousSGD(optim.Optimizer):
    """
    MaliciousSGD: Malicious Local Optimizer for Active Label Inference Attack in VFL.
    
    Implements Algorithm 1 from the Active Label Inference Attack paper.
    This optimizer amplifies gradients in consistent directions to make the
    bottom model's embeddings more informative for label inference.
    
    RESEARCH PURPOSE ONLY - For understanding VFL security vulnerabilities.
    
    Args:
        params: Model parameters to optimize
        lr (float): Learning rate (default: 0.01)
        beta (float): Momentum coefficient for velocity update (default: 0.9)
        gamma (float): Amplification factor for consistent gradients (default: 2.0)
        r_min (float): Minimum amplification ratio (default: 1.0)
        r_max (float): Maximum amplification ratio (default: 8.0)
    """

    def __init__(self, params, lr=0.01, beta=0.9, gamma=2.0, r_min=1.0, r_max=8.0):
        if lr < 0.0:
            raise ValueError(f"Invalid learning rate: {lr}")
        if not 0.0 <= beta < 1.0:
            raise ValueError(f"Invalid beta: {beta}")
        if gamma < 0.0:
            raise ValueError(f"Invalid gamma: {gamma}")
        if r_min > r_max:
            raise ValueError(f"r_min ({r_min}) must be <= r_max ({r_max})")

        defaults = dict(lr=lr, beta=beta, gamma=gamma, r_min=r_min, r_max=r_max)
        super(MaliciousSGD, self).__init__(params, defaults)

    def step(self, closure=None):
        """
        Performs a single malicious optimization step.
        
        Algorithm 1 - Malicious Local Optimizer:
        1. Compute velocity: v = beta*v + (1-beta)*g
        2. Compute amplification ratio: r = 1 + gamma * sign(v * v_last)
        3. Clamp ratio: r = clamp(r, r_min, r_max)
        4. Amplify velocity: v_amp = r * v
        5. Update weights: theta = theta - lr * v_amp
        6. Save v_amp as v_last for next step
        """
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        with torch.no_grad():
            for group in self.param_groups:
                lr    = group['lr']
                beta  = group['beta']
                gamma = group['gamma']
                r_min = group['r_min']
                r_max = group['r_max']

                for p in group['params']:
                    if p.grad is None:
                        continue

                    g_theta = p.grad.clone()  # current gradient

                    # NaN/Inf guard
                    if torch.isnan(g_theta).any() or torch.isinf(g_theta).any():
                        continue

                    # Norm clipping per-param
                    g_norm = g_theta.norm()
                    if g_norm > 1.0:
                        g_theta = g_theta * (1.0 / g_norm)

                    state = self.state[p]

                    # Initialize state on first call
                    if 'v_theta' not in state:
                        state['v_theta'] = torch.zeros_like(p)
                    if 'v_last' not in state:
                        state['v_last'] = torch.zeros_like(p)

                    v_theta = state['v_theta']
                    v_last  = state['v_last']

                    # Step 1 — Update velocity with momentum
                    v_theta.mul_(beta).add_(g_theta, alpha=(1.0 - beta))

                    # Step 2 — Compute amplification ratio based on direction consistency
                    sign_product = torch.sign(v_theta * v_last)   # {-1, 0, +1}
                    r_theta = 1.0 + gamma * sign_product

                    # Step 3 — Clamp ratio to [r_min, r_max]
                    r_theta = torch.clamp(r_theta, min=r_min, max=r_max)

                    # Step 4 — Amplify velocity
                    v_theta_amplified = r_theta * v_theta

                    # Clip velocity norm to avoid explosion
                    v_amp_norm = v_theta_amplified.norm()
                    if v_amp_norm > 1.0:
                        v_theta_amplified = v_theta_amplified * (1.0 / v_amp_norm)

                    # Step 5 — Update model weights
                    p.add_(v_theta_amplified, alpha=-lr)

                    # Step 6 — Persist state for next step
                    state['v_theta'].copy_(v_theta_amplified)
                    state['v_last'].copy_(v_theta)

        return loss


# ─────────────────────────────────────────────────────────────
#  Toy example: 3-layer MLP
# ─────────────────────────────────────────────────────────────

class ToyMLP(nn.Module):
    """Simple 3-layer MLP for demonstration."""
    def __init__(self, input_dim=20, hidden_dim=64, output_dim=2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x):
        return self.net(x)


def demo():
    torch.manual_seed(42)

    INPUT_DIM  = 20
    BATCH_SIZE = 32
    EPOCHS     = 10

    model     = ToyMLP(input_dim=INPUT_DIM)
    criterion = nn.CrossEntropyLoss()

    optimizer = MaliciousSGD(
        model.parameters(),
        lr=0.01,
        beta=0.9,
        gamma=2.0,
        r_min=1.0,
        r_max=8.0,
    )

    print("=" * 55)
    print("  MaliciousSGD — Active Label Inference Attack Demo")
    print("=" * 55)

    for epoch in range(1, EPOCHS + 1):
        input_data = torch.randn(BATCH_SIZE, INPUT_DIM)
        target     = torch.randint(0, 2, (BATCH_SIZE,))

        output = model(input_data)
        loss   = criterion(output, target)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if epoch % 2 == 0 or epoch == 1:
            first_param = next(model.parameters())
            state = optimizer.state[first_param]
            v_norm = state['v_theta'].norm().item() if 'v_theta' in state else 0.0
            print(f"  Epoch {epoch:02d} | loss = {loss.item():.4f} "
                  f"| ‖v_theta‖ = {v_norm:.4f}")

    print("=" * 55)
    print("Training complete.\n")


if __name__ == "__main__":
    demo()
