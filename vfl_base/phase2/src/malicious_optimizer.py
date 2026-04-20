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
        gamma (float): Amplification factor for consistent gradients (default: 1.0)
        r_min (float): Minimum amplification ratio (default: 1.0)
        r_max (float): Maximum amplification ratio (default: 5.0)
    """

    def __init__(self, params, lr=0.01, beta=0.9, gamma=1.0, r_min=1.0, r_max=5.0):
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

    @torch.no_grad()
    def step(self, closure=None):
        """
        Performs a single malicious optimization step.
        
        Algorithm 1 - Malicious Local Optimizer:
        1. Compute velocity: v = beta*v + (1-beta)*g
        2. Save previous velocity: v_last = v
        3. Compute amplification ratio: r = 1 + gamma * sign(v * v_last)
        4. Clamp ratio: r = clamp(r, r_min, r_max)
        5. Amplify velocity: v = r * v_last
        6. Update weights: theta = theta - lr * v
        """
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        for group in self.param_groups:
            lr    = group['lr']
            beta  = group['beta']
            gamma = group['gamma']
            r_min = group['r_min']
            r_max = group['r_max']

            for p in group['params']:
                if p.grad is None:
                    continue

                g_theta = p.grad  # current gradient

                state = self.state[p]

                # Step 1 — Initialize velocity to zero on first call
                # Bước 1 — Khởi tạo vector vận tốc bằng 0 ở lần đầu tiên
                if 'v_theta' not in state:
                    state['v_theta'] = torch.zeros_like(p)
                if 'v_last' not in state:
                    state['v_last'] = torch.zeros_like(p)

                v_theta = state['v_theta']
                v_last = state['v_last']  # PREVIOUS step velocity

                # Step 2 — Update velocity with momentum
                # Bước 2 — Cập nhật vận tốc với momentum
                # v_theta = beta * v_theta + (1 - beta) * g_theta
                v_theta.mul_(beta).add_(g_theta, alpha=(1.0 - beta))

                # Step 3 — Compute amplification ratio BEFORE updating v_last
                # Bước 3 — Tính tỷ lệ khuếch đại dựa trên dấu của tích v_theta * v_last
                # r_theta = 1.0 + gamma * sign(v_theta * v_last)
                # Now correctly computes sign(new_v * prev_v) for direction consistency
                sign_product = torch.sign(v_theta * v_last)           # {-1, 0, +1}
                r_theta = 1.0 + gamma * sign_product                  # amplification ratio

                # Step 4 — Clamp ratio to [r_min, r_max]
                # Bước 4 — Ràng buộc tỷ lệ trong khoảng [r_min, r_max]
                r_theta = torch.clamp(r_theta, min=r_min, max=r_max)

                # Step 5 — Amplify velocity
                # Bước 5 — Khuếch đại vận tốc
                # v_theta = r_theta * v_last
                v_theta_amplified = r_theta * v_theta  # Apply amplification to updated velocity

                # Step 6 — Update model weights
                # Bước 6 — Cập nhật trọng số mô hình
                # theta = theta - lr * v_theta
                p.add_(v_theta_amplified, alpha=-lr)

                # Step 7 — Persist current velocity for next step
                # Bước 7 — Lưu vận tốc hiện tại cho bước tiếp theo
                state['v_theta'].copy_(v_theta_amplified)
                state['v_last'].copy_(v_theta)  # Save updated velocity for next iteration
                # theta = theta - lr * v_theta
                p.add_(v_theta_amplified, alpha=-lr)

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

    # ── Hyper-parameters ──────────────────────────────────────
    INPUT_DIM  = 20
    BATCH_SIZE = 32
    EPOCHS     = 10

    model     = ToyMLP(input_dim=INPUT_DIM)
    criterion = nn.CrossEntropyLoss()

    # ── Drop-in replacement for torch.optim.SGD ───────────────
    optimizer = MaliciousSGD(
        model.parameters(),
        lr=0.01,
        beta=0.9,
        gamma=1.0,
        r_min=1.0,
        r_max=5.0,
    )

    print("=" * 55)
    print("  MaliciousSGD — Active Label Inference Attack Demo")
    print("=" * 55)

    for epoch in range(1, EPOCHS + 1):
        input_data = torch.randn(BATCH_SIZE, INPUT_DIM)
        target     = torch.randint(0, 2, (BATCH_SIZE,))

        output = model(input_data)
        loss   = criterion(output, target)

        optimizer.zero_grad()   # standard: clear gradients
        loss.backward()         # compute gradients
        optimizer.step()        # ← malicious update applied here

        if epoch % 2 == 0 or epoch == 1:
            # Show amplification stats for first param group
            first_param = next(model.parameters())
            v = MaliciousSGD.__dict__   # just reference; real state below
            state = optimizer.state[first_param]
            v_norm = state['v_theta'].norm().item() if 'v_theta' in state else 0.0
            print(f"  Epoch {epoch:02d} | loss = {loss.item():.4f} "
                  f"| ‖v_theta‖ = {v_norm:.4f}")

    print("=" * 55)
    print("Training complete.\n")

    # ── How to replace SGD in an existing VFL training file ───
    print("To replace SGD in your VFL bottom-model trainer:")
    print("  # Before:")
    print("  optimizer = torch.optim.SGD(bottom_model.parameters(), lr=0.01)")
    print()
    print("  # After (one-line change):")
    print("  optimizer = MaliciousSGD(bottom_model.parameters(),")
    print("                           lr=0.01, beta=0.9, gamma=1.0,")
    print("                           r_min=1.0, r_max=5.0)")
    print()
    print("All subsequent optimizer.zero_grad() / loss.backward() /")
    print("optimizer.step() calls remain exactly the same.")


if __name__ == "__main__":
    demo()
