import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def verify_imports():
    core_libs = [
        ('ultralytics', 'YOLOv8 Detection'),
        ('supervision', 'ByteTrack / Annotations'),
        ('cv2', 'OpenCV'),
        ('chromadb', 'Vector DB'),
        ('sentence_transformers', 'Embeddings'),
        ('google.generativeai', 'Gemini API'),
        ('groq', 'Groq API'),
        ('gradio', 'Gradio UI')
    ]
    
    failed = []
    
    for module_name, desc in core_libs:
        try:
            __import__(module_name)
        except ImportError:
            failed.append(f"{desc} ({module_name})")
            
    if failed:
        logging.error("The following core libraries failed to import:")
        for f in failed:
            logging.error(f"  - {f}")
        logging.error("Please ensure you have activated your virtual environment and run 'pip install -r requirements.txt'")
    else:
        logging.info("✅ All core libraries imported successfully!")

if __name__ == "__main__":
    verify_imports()
