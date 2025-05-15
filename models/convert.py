import torch

# Load the full checkpoint
checkpoint = torch.load("mobilefacenet.pt", map_location="cpu")

# Check if it's wrapped inside 'state_dict'
if "state_dict" in checkpoint:
    state_dict = checkpoint["state_dict"]
else:
    state_dict = checkpoint

# Save only the state_dict
torch.save(state_dict, "mobilefacenet_clean.pt")

print("✅ Converted and saved as 'mobilefacenet_clean.pt'")
