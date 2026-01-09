# Engineering Deep Dive: Blood Cell Analysis Platform

## 1. Data Flow and Frappe Integration

The platform is built on the Frappe framework, a full-stack web framework that provides a robust backend, a user-friendly UI, and a powerful ORM. The data flow is orchestrated through a series of Frappe DocTypes and API endpoints.

**DocTypes:**

*   **Patient:** Stores patient information.
*   **Blood Smear Image:** Stores the uploaded blood smear image and links to a Patient.
*   **Cell Detection Image:** Stores the image with bounding boxes drawn around detected cells, and links to the Blood Smear Image. It also contains a child table, **Detection Result**, which stores the classification, confidence score, and bounding coordinates for each detected cell.
*   **Extracted Cell:** Stores the cropped image of a single cell, its primary classification, and a link to the Cell Detection Image. It also stores the XAI image.
*   **Patient Report:** Stores the final report, including a summary of the analysis and a link to the Patient.

**API Endpoints:**

*   `/api/method/medical_imaging.api.cell_detection.detect_cells`: This endpoint receives a `blood_smear_id` and initiates the cell detection process.
*   `/api/method/medical_imaging.api.cell_extraction.extract_cells`: This endpoint receives a `cell_detection_image_id` and extracts each detected cell into a separate `Extracted Cell` document.
*   `/api/method/medical_imaging.api.classification.enqueue_classification`: This endpoint receives a `cell_detection_image_id` and enqueues a background job to classify all the extracted cells.

**Workflow:**

1.  A user uploads a blood smear image, creating a **Blood Smear Image** document.
2.  The user triggers the analysis, which calls the `detect_cells` API.
3.  The `detect_cells` API creates a **Cell Detection Image** document and populates the **Detection Result** child table.
4.  The frontend then calls the `extract_cells` API, which creates an **Extracted Cell** document for each detected cell.
5.  Finally, the frontend calls the `enqueue_classification` API, which enqueues a background job to classify all the extracted cells.
6.  The background job updates each **Extracted Cell** document with the validated classification and the XAI image.

## 2. Machine Learning Pipeline

The machine learning pipeline consists of two main components: a cell detection model and a cell classification model.

**Cell Detection:**

*   **Model:** Faster R-CNN with a ResNet-50 backbone.
*   **Framework:** PyTorch.
*   **Input:** A blood smear image.
*   **Output:** A list of bounding boxes, labels, and confidence scores for each detected cell.
*   **Implementation:** The `get_predictions` function in `medical_imaging/api/cell_detection.py` loads the pre-trained model, performs inference on the input image, and returns the predictions.

**Cell Classification:**

*   **Model:** EfficientNetB4.
*   **Framework:** PyTorch.
*   **Input:** A cropped image of a single cell.
*   **Output:** A classification label (e.g., "Circular", "Elongated", "Other").
*   **Implementation:** The `classify_extracted_cell` function in `medical_imaging/api/classification.py` loads the pre-trained model, performs inference on the input image, and returns the classification.

## 3. Explainable AI (XAI)

To provide transparency and build trust in the AI's predictions, we use Grad-CAM (Gradient-weighted Class Activation Mapping) to generate heatmaps that highlight the regions of the image that were most influential in the model's decision.

*   **Implementation:** The `GradCAM` class in `medical_imaging/api/classification.py` implements the Grad-CAM algorithm. The `classify_extracted_cell` function uses this class to generate a heatmap for each classified cell, which is then overlaid on the original cell image and saved as the XAI image.
