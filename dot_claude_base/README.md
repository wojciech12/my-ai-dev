# Notification


## Sound notifications

https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/CLI.md

```bash
uv pip install piper-tts


mkdir -p ~/.config/piper-tts/models

python3 -m piper.download_voices en_US-libritts-high --data-dir ~/.config/piper-tts/models

```

Add to your zshrc:

```bash
export PIPER_DATA_DIR= ~/.config/piper-tts/models
```
