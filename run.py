import argparse
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description="AegisIDS Control CLI")
    parser.add_argument("--api", action="store_true", help="Launch FastAPI Backend Server")
    parser.add_argument("--expo", action="store_true", help="Launch Expo Mobile/Web Frontend")
    parser.add_argument("--dashboard", action="store_true", help="Launch Streamlit Security Dashboard (Legacy)")
    parser.add_argument("--train-all", action="store_true", help="Run end-to-end training pipeline")
    parser.add_argument("--experiments", action="store_true", help="Run comprehensive experimental evaluation suite")
    parser.add_argument("--test", action="store_true", help="Run unit tests")
    
    args = parser.parse_args()
    
    if args.api:
        print("Launching AegisIDS FastAPI Server on http://127.0.0.1:8000 ...")
        subprocess.run([sys.executable, "-m", "uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])
    elif args.expo:
        print("Launching AegisIDS Expo Frontend...")
        subprocess.run(["npx", "expo", "start"], cwd=str(BASE_DIR / "expo-app"))
    elif args.dashboard:
        print("Launching AegisIDS Streamlit Dashboard...")
        subprocess.run(["streamlit", "run", str(BASE_DIR / "dashboard" / "app.py")])
    elif args.train_all:
        subprocess.run([sys.executable, str(BASE_DIR / "src" / "data" / "download_dataset.py")], check=True)
        print("[2/5] Preprocessing Data...")
        subprocess.run([sys.executable, str(BASE_DIR / "src" / "preprocessing" / "preprocessor.py")], check=True)
        print("[3/5] Feature Selection & Baselines...")
        subprocess.run([sys.executable, str(BASE_DIR / "src" / "features" / "feature_selection.py")], check=True)
        subprocess.run([sys.executable, str(BASE_DIR / "src" / "models" / "baseline_models.py")], check=True)
        print("[4/5] Training DNN & Autoencoder...")
        subprocess.run([sys.executable, str(BASE_DIR / "src" / "models" / "dnn_classifier.py")], check=True)
        subprocess.run([sys.executable, str(BASE_DIR / "src" / "anomaly" / "autoencoder.py")], check=True)
        print("[5/5] Running Experiments & Evaluation...")
        subprocess.run([sys.executable, str(BASE_DIR / "run_experiments.py")], check=True)
        print("All steps completed successfully!")
    elif args.experiments:
        print("Running Experimental Suite...")
        subprocess.run([sys.executable, str(BASE_DIR / "run_experiments.py")], check=True)
    elif args.test:
        print("Running Unit Tests...")
        subprocess.run([sys.executable, str(BASE_DIR / "tests" / "test_pipeline.py")], check=True)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
