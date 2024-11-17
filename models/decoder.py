import torch
import torch.nn as nn
import torch.nn.functional as F

# paralled decoder test stuff:
class DecoderLayer(nn.Module):
    def __init__(self, cross_attention, d_model, d_ff=None, dropout=0.1, activation="relu"):
        super(DecoderLayer, self).__init__()
        d_ff = d_ff or 4 * d_model
        self.cross_attention = cross_attention
        self.conv1 = nn.Conv1d(in_channels=d_model, out_channels=d_ff, kernel_size=1)
        self.conv2 = nn.Conv1d(in_channels=d_ff, out_channels=d_model, kernel_size=1)
        self.conv3 = nn.Conv1d(in_channels=d_ff, out_channels=d_model, kernel_size=1)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
        self.activation = F.relu if activation == "relu" else F.gelu

    def forward(self, x, cross, cross_mask=None):
        # Cross-attention without autoregressive constraints
        x = x + self.dropout(self.cross_attention(
            x, cross, cross, attn_mask=cross_mask
        )[0])
        x = self.norm1(x)

        # Feed-forward layer
        y = self.dropout(self.activation(self.conv1(x.transpose(-1, 1))))
        y = self.dropout(self.conv2(y).transpose(-1, 1))
        return self.norm2(x + y)

class Decoder(nn.Module):
    def __init__(self, layers, norm_layer=None):
        super(Decoder, self).__init__()
        self.layers = nn.ModuleList(layers)
        self.norm = norm_layer

    def forward(self, x, cross, cross_mask=None):
        for layer in self.layers:
            x = layer(x, cross, cross_mask=cross_mask)

        if self.norm is not None:
            x = self.norm(x)

        return x
