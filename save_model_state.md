# Save & Restore Optimizer State — Implementation Guide

## Current State (What Already Works)

`rl_solver.py → RLSolver.save_model()` already saves optimizer state correctly:

```python
# rl_solver.py line ~260 — already correct, no changes needed
def save_model(self, checkpoint_fname):
    checkpoint_fname = os.path.join(self.model_dir, checkpoint_fname)
    torch.save({
        'policy': self.policy.state_dict(),
        'optimizer': self.optimizer.state_dict(),
    }, checkpoint_fname)
```

The `.pkl` files on disk already contain the optimizer state. ✅

---

## Problem 1: `load_model` doesn't return the saved epoch

`rl_solver.py → RLSolver.load_model()` loads weights and optimizer but **throws away the epoch number**, so `learn()` always restarts from `start_epoch=0`.

### Fix — add `epoch` to save, return it on load

**In `save_model`**, pass the current epoch in:

```python
# rl_solver.py — replace save_model with this
def save_model(self, checkpoint_fname, epoch=None):
    checkpoint_fname = os.path.join(self.model_dir, checkpoint_fname)
    torch.save({
        'policy': self.policy.state_dict(),
        'optimizer': self.optimizer.state_dict(),
        'epoch': epoch,                          # ← ADD THIS
    }, checkpoint_fname)
    print(f'Save model to {checkpoint_fname}\n') if self.verbose >= 0 else None
```

**In `load_model`**, extract and return the epoch:

```python
# rl_solver.py — replace load_model with this
def load_model(self, checkpoint_path):
    print('Attempting to load the pretrained model')
    start_epoch = 0
    try:
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        if 'policy' not in checkpoint:
            # legacy format: plain state_dict (old .pkl files)
            self.policy.load_state_dict(checkpoint)
        else:
            self.policy.load_state_dict(checkpoint['policy'])
            self.optimizer.load_state_dict(checkpoint['optimizer'])
            if checkpoint.get('epoch') is not None:
                start_epoch = checkpoint['epoch'] + 1   # resume AFTER saved epoch
        print(f'Loaded pretrained model from {checkpoint_path}, resuming from epoch {start_epoch}') if self.verbose >= 0 else None
    except Exception as e:
        print(f'Load failed: {e}\nInitialized with random parameters') if self.verbose >= 0 else None
    return start_epoch
```

---

## Problem 2: `learn()` ignores the returned start_epoch

`OnlineAgent.learn()` in `rl_solver.py` takes `start_epoch` as a parameter but the caller (BasicScenario or your training script) passes 0.

### Fix — wire start_epoch through the call chain

**Step 1:** In `OnlineAgent.learn()`, the signature is already correct — no changes needed:
```python
def learn(self, env, num_epochs=1, start_epoch=0, ...):
    for epoch_id in range(start_epoch, start_epoch + num_epochs):  # already correct ✅
```

**Step 2:** Wherever `learn()` is called (likely `base/scenario.py` or your main training loop), capture the returned `start_epoch` from `load_model` and pass it in:

```python
# In BasicScenario.run() or wherever training is launched — find this pattern:
if config.pretrained_model_path not in [None, '']:
    solver.load_model(config.pretrained_model_path)   # ← currently ignores return value
solver.learn(env, num_epochs=config.num_train_epochs)

# Change to:
start_epoch = 0
if config.pretrained_model_path not in [None, '']:
    start_epoch = solver.load_model(config.pretrained_model_path)  # ← capture epoch
solver.learn(env, num_epochs=config.num_train_epochs, start_epoch=start_epoch)
```

---

## Problem 3: `save_model` call inside `learn()` doesn't pass the epoch

Inside `OnlineAgent.learn()`, the save call currently does:
```python
self.save_model(f'model-{epoch_id}.pkl')   # epoch not stored inside checkpoint
```

Change to:
```python
self.save_model(f'model-{epoch_id}.pkl', epoch=epoch_id)   # ← pass epoch
```

Same fix applies to `InstanceAgent.learn()` around line ~130 in `rl_solver.py`.

---

## Problem 4: Optimizer device mismatch after loading

When loading a checkpoint saved on GPU onto CPU (or vice versa), Adam's internal moment tensors stay on the wrong device and crash on the first `optimizer.step()`.

Add this right after `self.optimizer.load_state_dict(...)`:

```python
# In load_model, after loading optimizer state:
self.optimizer.load_state_dict(checkpoint['optimizer'])

# Move optimizer state tensors to correct device
for state in self.optimizer.state.values():
    for k, v in state.items():
        if isinstance(v, torch.Tensor):
            state[k] = v.to(self.device)
```

---

## Optional: Save RunningMeanStd stats (reward normalization)

`HrlAcSolver` uses `norm_reward=True`, which means `RunningMeanStd` accumulates statistics across epochs. These are lost on reload, causing the reward baseline to reset.

```python
# In save_model — add to the dict:
torch.save({
    'policy': self.policy.state_dict(),
    'optimizer': self.optimizer.state_dict(),
    'epoch': epoch,
    'running_stats': {                                      # ← ADD
        'mean': self.running_stats.mean,
        'var': self.running_stats.var,
        'count': self.running_stats.count,
    } if hasattr(self, 'running_stats') else None,
}, checkpoint_fname)

# In load_model — restore after loading optimizer:
if checkpoint.get('running_stats') is not None and hasattr(self, 'running_stats'):
    rs = checkpoint['running_stats']
    self.running_stats.mean  = rs['mean']
    self.running_stats.var   = rs['var']
    self.running_stats.count = rs['count']
```

---

## Summary of all files to touch

| File | Method | Change |
|------|--------|--------|
| `solver/learning/rl_solver.py` | `RLSolver.save_model` | Add `epoch=None` param, store in dict |
| `solver/learning/rl_solver.py` | `RLSolver.load_model` | Extract epoch, fix device, return `start_epoch` |
| `solver/learning/rl_solver.py` | `OnlineAgent.learn` | Change save call to `save_model(fname, epoch=epoch_id)` |
| `solver/learning/rl_solver.py` | `InstanceAgent.learn` | Same save call fix |
| `base/scenario.py` (or equivalent) | `run()` / training entry | Capture `load_model` return, pass to `learn(start_epoch=...)` |

---

## Verifying it works

After your next save, inspect the checkpoint:
```python
import torch
ckpt = torch.load('save/hrl_ac/.../model/model-7.pkl')
print(ckpt.keys())           # should show: policy, optimizer, epoch, running_stats
print(ckpt['epoch'])         # should show: 7
print(ckpt['optimizer']['state'].keys())  # non-empty = optimizer state saved
```

If `ckpt['optimizer']['state']` is an empty dict `{}`, it means the model was saved before any gradient step occurred (e.g. loaded a pretrained model and saved immediately without training). That's fine — optimizer state will populate after the first `update()` call.
