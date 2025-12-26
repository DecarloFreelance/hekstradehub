# HekTradeHub Auto-Activation Setup

## Option 1: Automatic with direnv (RECOMMENDED)

**Install direnv:**
```bash
sudo apt install direnv
```

**Add to ~/.bashrc:**
```bash
eval "$(direnv hook bash)"
```

**Allow the directory:**
```bash
cd /home/hektic/hekstradehub
direnv allow
```

Now the venv will auto-activate whenever you `cd` into this directory!

---

## Option 2: Manual - Add to ~/.bashrc

Add this code to your `~/.bashrc`:

```bash
# Auto-activate HekTradeHub venv
cd() {
    builtin cd "$@"
    if [[ "$PWD" == /home/hektic/hekstradehub* ]] && [[ -f .venv/bin/activate ]]; then
        if [[ "$VIRTUAL_ENV" != "$PWD/.venv" ]]; then
            source .venv/bin/activate
        fi
    fi
}
```

Then reload: `source ~/.bashrc`

---

## Option 3: Just use the launchers (EASIEST)

The `./trade` and `./status` scripts already activate the venv automatically!

```bash
./trade    # Main dashboard (auto-activates)
./status   # Quick check (auto-activates)
```

No configuration needed!

---

## Current Status

✓ Virtual environment: `.venv/` (376M, 46 packages)
✓ Launchers ready: `./trade`, `./status`  
✓ direnv config created: `.envrc`
