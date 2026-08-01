from torch.nn.functional import log_softmax, pad

# tensor掩码
scores = scores.masked_fill(mask == 0, -1e9)

pad(
        processed_src,
        (
            0,
            max_padding - len(processed_src),
        ),
        value=pad_id,
    )