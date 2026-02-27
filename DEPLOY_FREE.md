# Deploy StoryForge for Free

Two ways to run StoryForge in the cloud for free (no need for your own GPU).

---

## Option 1: Google Colab (free GPU, run in a notebook)

Best for: running the **full pipeline** with **real image generation** using a free GPU.

1. **Open Google Colab:** [colab.research.google.com](https://colab.research.google.com)

2. **New notebook** → in the first cell, run:

```python
# Clone your repo (replace with your GitHub repo if you pushed StoryForge there)
!git clone https://github.com/YOUR_USERNAME/StoryForgeAI.git
%cd StoryForgeAI/python_service

# Enable GPU: Runtime → Change runtime type → T4 GPU (free)
# Then install deps
!pip install -r requirements-minimal.txt
!pip install gradio
# For real images (optional, uses more GPU time):
# !pip install torch diffusers transformers accelerate
# Then set IMAGE_BACKEND=huggingface in the next cell
```

3. **Run the pipeline** in a new cell:

```python
import os
os.environ["IMAGE_BACKEND"] = "placeholder"  # or "huggingface" if you installed full deps

from run_storyforge import main
import sys
sys.argv = ["run_storyforge.py", "The sun set over the lighthouse. Maya walked on the shore."]
main()
```

4. **Download the video** from the `output/` folder in the file panel (left sidebar).

- **Free tier:** GPU time is limited per day; when it runs out, use CPU (slower) or wait.
- To use **your own repo**, push StoryForge to GitHub and replace the `git clone` URL.

---

## Option 2: Hugging Face Spaces (free web app, shareable)

Best for: a **public web page** where anyone can paste a story and get a video. Runs on CPU with **placeholder images** by default. In the app you can switch to **Hugging Face (real images)**; on free CPU it may be slow or run out of memory.

### A. Deploy from the Hugging Face website

1. **Create an account:** [huggingface.co/join](https://huggingface.co/join)

2. **Create a new Space:**  
   [huggingface.co/new-space](https://huggingface.co/new-space)  
   - Name: e.g. `StoryForge`  
   - SDK: **Gradio**  
   - Hardware: **CPU basic** (free)

3. **Clone your Space** (git), then add these files:

**`app.py`** (replace the default):

```python
# Clone or copy your StoryForge python_service contents into the Space repo, then:
import sys
sys.path.insert(0, "/app/python_service")
import os
os.environ["IMAGE_BACKEND"] = "placeholder"
from app_gradio import main
main()
```

**Or** upload your whole `python_service` folder into the Space repo and in `app.py` do:

```python
import sys, os
os.environ["IMAGE_BACKEND"] = "placeholder"
sys.path.insert(0, "python_service")
from app_gradio import main
main()
```

4. **Requirements:** In the Space repo, use a `requirements.txt` at the **repo root** with:

```
gradio
openai>=1.0.0
edge-tts>=6.1.0
moviepy>=1.0.3
Pillow>=10.0.0
imageio>=2.31.0
imageio-ffmpeg>=0.4.9
pydub>=0.25.0
python-dotenv>=1.0.0
pydantic>=2.0.0
```

5. **Repo layout:** Your Space repo should have at the root: **`app.py`**, **`requirements.txt`**, and the **`python_service/`** folder (with `run_storyforge.py`, `app_gradio.py`, `storyforge/`, etc.). The root **`app.py`** (included in StoryForge) launches the Gradio UI.

6. **Push to the Space.** Hugging Face will build and run the app. Your app URL will be:  
   `https://huggingface.co/spaces/YOUR_USERNAME/StoryForge`

### B. Or run the Gradio app locally (no deploy)

```bash
cd python_service
pip install -r requirements-minimal.txt
pip install gradio
python app_gradio.py
```

Then open **http://127.0.0.1:7860** in your browser.

---

## Why placeholder by default?

On **free** Hugging Face Spaces (CPU, limited RAM):

- **Placeholder** = no Stable Diffusion, low RAM, no timeout. The app always works.
- **Hugging Face** = loads Stable Diffusion (~4GB+). On free CPU it can run out of memory (OOM) or hit the request time limit (each image can take minutes).

We default to **placeholder** so the Space stays within the free tier. You can still choose **Hugging Face (real images)** in the web UI: on a **GPU Space** it works well; on **CPU** it may work with short stories but can be slow or OOM.

---

## Summary

| Method              | Cost   | GPU        | Best for                          |
|---------------------|--------|------------|------------------------------------|
| **Google Colab**    | Free   | Free tier  | Full pipeline, real images, you run when you want |
| **Hugging Face Space** | Free | CPU default; optional GPU | Web app; choose Placeholder or Hugging Face in the UI |
| **Local (your PC)** | Free   | If you have one | Full control, no time limits        |


To **deploy for free**, use **Colab** for “run in the cloud with GPU” and **Hugging Face Spaces** for “share a free web app." In the app, pick **Hugging Face (real images)** when you want generated scenes instead of placeholder cards.
