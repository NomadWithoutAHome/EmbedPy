# EmPy - Image File Embedder

A modern web application that allows you to securely embed any file into an image using LSB (Least Significant Bit) steganography. Built with FastAPI and styled with a retro-tech aesthetic using Tailwind CSS.

## Features

- Embed any file into a carrier image
- Extract previously embedded files from images
- Modern, responsive UI with retro-tech design
- Drag-and-drop file upload support
- Secure file handling
- Real-time feedback

## Technical Details

The application uses LSB (Least Significant Bit) steganography to embed files into images. This technique modifies the least significant bits of the image's RGB values to store the file data, making the changes virtually imperceptible to the human eye.

## Requirements

- Python 3.8+
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd empy
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

2. Open your browser and navigate to:
```
http://localhost:8000
```

## Usage

### Embedding a File

1. Click or drag an image to the "Carrier Image" upload zone
2. Click or drag any file to the "File to Embed" upload zone
3. Click "INITIATE EMBEDDING SEQUENCE"
4. Save the resulting image file

### Extracting a File

1. Click or drag an image containing an embedded file to the "Embedded Image" upload zone
2. Click "INITIATE EXTRACTION SEQUENCE"
3. Save the extracted file

## Security Considerations

- The embedded data is not encrypted by default
- The carrier image should be large enough to hold the file you want to embed
- PNG format is used for output to prevent data loss from compression

## License

MIT License - Feel free to use this project for any purpose.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 