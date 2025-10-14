# Jupyter Notebooks

Interactive tutorials explaining the biometric DID system's algorithms and implementation.

## 📚 Available Notebooks

### 1. Biometric DID Tutorial (`biometric-did-tutorial.ipynb`)
**Difficulty**: Beginner to Intermediate  
**Duration**: 30-45 minutes

Comprehensive walkthrough of the complete biometric DID pipeline with visualizations.

**Topics covered:**
1. **Minutiae Extraction** - Understanding fingerprint features
2. **Quantization** - Grid-based normalization for reproducibility
3. **Fuzzy Extraction** - Error-tolerant digest generation
4. **Multi-Finger Aggregation** - XOR-based combination
5. **DID Generation** - W3C-compliant identifiers
6. **Security Analysis** - Reproducibility, uniqueness, non-invertibility tests

**What you'll learn:**
- How fingerprint scanners extract minutiae points
- Why quantization is necessary for noisy biometric data
- How BCH error correction enables fuzzy extraction
- Why multi-finger aggregation provides 256-bit security
- How to verify security properties programmatically

**Prerequisites:**
```bash
pip install -e .
pip install jupyter matplotlib numpy
```

**Run it:**
```bash
jupyter notebook notebooks/biometric-did-tutorial.ipynb
```

---

## 🚀 Quick Start

### Install Dependencies
```bash
# Core toolkit
pip install -e .

# Notebook dependencies
pip install jupyter matplotlib numpy pandas
```

### Launch Jupyter
```bash
# Start Jupyter Lab (recommended)
jupyter lab

# Or classic notebook
jupyter notebook
```

Then navigate to `notebooks/` and open a tutorial.

---

## 📊 Visualizations

These notebooks include rich visualizations:

1. **Minutiae plots**: Scatter plots showing fingerprint feature points
2. **Quantization effects**: Before/after grid alignment
3. **Entropy scaling**: Security levels by finger count
4. **Helper data analysis**: Shannon entropy calculations
5. **Performance metrics**: Timing and throughput benchmarks

All plots are generated with `matplotlib` and `numpy`.

---

## 🎓 Learning Path

**For beginners:**
1. Start with `biometric-did-tutorial.ipynb`
2. Run each cell sequentially
3. Experiment with parameters (grid size, angle bins)
4. Visualize your own minutiae data

**For advanced users:**
1. Study the security analysis sections
2. Modify aggregation algorithms
3. Implement custom storage backends
4. Benchmark performance variations

---

## 🛠️ Customization

### Use Your Own Data

Replace sample minutiae with real fingerprint scanner output:

```python
# Load from JSON
import json
with open('your_fingerprints.json') as f:
    data = json.load(f)

minutiae = [
    Minutia(x=m['x'], y=m['y'], angle=m['angle'])
    for m in data['minutiae']
]
```

### Adjust Parameters

Experiment with different quantization settings:

```python
# Coarser grid (more noise tolerance, less precision)
template = FingerTemplate(
    finger_id="thumb",
    minutiae=minutiae,
    grid_size=20.0,  # Default: 10.0
    angle_bins=4     # Default: 8
)

# Finer grid (less noise tolerance, more precision)
template = FingerTemplate(
    finger_id="thumb",
    minutiae=minutiae,
    grid_size=5.0,
    angle_bins=16
)
```

### Add Your Own Analysis

Extend notebooks with custom tests:

```python
# Test error correction limits
def test_error_tolerance():
    for error_count in range(1, 15):
        # Add artificial errors
        noisy_template = add_noise(template, error_count)
        
        # Try to reproduce
        try:
            verified = extractor.reproduce(noisy_template, helper)
            print(f"{error_count} errors: ✅ Reproduced")
        except Exception as e:
            print(f"{error_count} errors: ❌ Failed ({e})")
```

---

## 📖 Related Resources

- **API Reference**: `docs/SDK.md` - Complete SDK documentation
- **Shell Demos**: `demos/` - Interactive terminal demonstrations
- **Examples**: `examples/sdk_demo.py` - Working code samples
- **Architecture**: `docs/architecture.md` - System design overview

---

## 🐛 Troubleshooting

### "Kernel not found"
Install Jupyter kernel for the correct Python environment:
```bash
python -m ipykernel install --user --name=decentralized-did
```

### "Module not found: decentralized_did"
Install toolkit in development mode:
```bash
pip install -e .
```

### "matplotlib not available"
Install visualization dependencies:
```bash
pip install matplotlib numpy pandas
```

### Plots not showing
Ensure matplotlib backend is configured:
```python
%matplotlib inline  # Add to first cell
```

---

## 🤝 Contributing

Want to add more notebooks?

### Creating a New Notebook

1. **Choose a topic**: Focus on one specific algorithm or use case
2. **Structure**: Introduction → Theory → Implementation → Visualization → Exercises
3. **Code cells**: Keep short (5-15 lines), add comments
4. **Markdown cells**: Explain concepts clearly, use analogies
5. **Visualizations**: Include at least 2-3 plots
6. **Exercises**: Add "Try it yourself" sections

### Notebook Template

```markdown
# Notebook Title

Brief description of what this tutorial covers.

## Prerequisites
- Concepts to understand first
- Required installations

## Part 1: Theory
Explain the concept...

## Part 2: Implementation
Show the code...

## Part 3: Visualization
Create plots...

## Part 4: Exercises
Try modifying...

## Summary
Recap what was learned...
```

### Best Practices

- ✅ Clear cell outputs (run before committing)
- ✅ Add cell numbers for easy reference
- ✅ Include estimated completion time
- ✅ Test on fresh Python environment
- ✅ Use consistent styling (PEP 8)
- ✅ Add "Try it yourself" sections
- ✅ Link to relevant documentation

See `.github/copilot-instructions.md` for coding standards.

---

## 📝 Citation

If you use these notebooks in research or education, please cite:

```bibtex
@misc{biometric-did-notebooks,
  title={Biometric DID Generation: Interactive Tutorials},
  author={Decentralized DID Project},
  year={2024},
  url={https://github.com/yourusername/decentralized-did/tree/main/notebooks}
}
```

---

## 📜 License

Apache 2.0 - See [LICENSE](../LICENSE) for details.
