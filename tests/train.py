import argparse

parser = argparse.ArgumentParser(description="Train a model")
parser.add_argument("--a", type=float, default=0.01)
parser.add_argument("--b", type=float, default=10)
args = parser.parse_args()


if __name__ == "__main__":
    print(f"Running with args: {args}")
    print("Done")
