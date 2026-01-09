# Solution Architecture: AI-Powered Medical Imaging Platform

## 1. High-Level Architecture

The application is designed as a **monolithic system** built upon the Frappe framework. This approach was chosen to simplify development, deployment, and maintenance for the initial product. The architecture follows a standard client-server model, with a clear separation of concerns between the user interface, backend logic, and the machine learning pipeline.

*   **Client-Side (Frontend):** The user interface is provided by Frappe's standard Desk UI, which is a responsive, data-driven single-page application.
*   **Server-Side (Backend):** The Frappe framework serves as the core of the backend, handling:
    *   **Business Logic:** Managing the workflow from patient creation to report generation.
    *   **Data Persistence:** Using DocTypes as an Object-Relational Mapper (ORM) to interact with the database.
    *   **API Layer:** Exposing RESTful API endpoints for the client to interact with the machine learning models.
    *   **Authentication & Authorization:** Leveraging Frappe's built-in user management and role-based permissions.
*   **Machine Learning Pipeline:** The ML models are integrated into the Frappe application and are invoked through dedicated API endpoints. To ensure the application remains responsive, the most computationally intensive tasks are offloaded to a background worker queue.

## 2. Technology Stack

*   **Backend Framework:** Frappe
*   **Programming Language:** Python
*   **Database:** MariaDB (Frappe's default database)
*   **Frontend:** Frappe Desk UI (Vue.js, JavaScript, HTML, CSS)
*   **Machine Learning:**
    *   **Core Library:** PyTorch
    *   **Detection Model:** Faster R-CNN (`torchvision`)
    *   **Classification Model:** EfficientNetB4 (`timm`)
*   **Deployment:** Docker

## 3. Key Architectural Strategies

*   **Monolithic Architecture:** Simplifies initial development and deployment. The system is a single, self-contained unit.
*   **MVC-like Pattern:** Frappe's architecture, with DocTypes (Models), UI Views (Views), and Python API/Controller logic, provides a structured approach to development.
*   **Asynchronous Processing:** The classification of individual cells is a time-consuming process. To avoid blocking the user interface and improve user experience, this task is handled asynchronously using Frappe's built-in background job queue (`frappe.enqueue`).
*   **Scalability:** The current monolithic architecture is suitable for the initial phase. For future growth, the system is designed to be scalable:
    *   **Decoupling ML Services:** The machine learning models can be extracted into separate microservices and exposed via a dedicated API gateway.
    *   **Horizontal Scaling:** Frappe can be scaled horizontally by running multiple instances behind a load balancer.
    *   **Database Scaling:** The MariaDB database can be scaled independently to handle increased load.
*   **Explainable AI (XAI):** The integration of Grad-CAM is a core architectural principle. It provides transparency into the model's decision-making process, which is crucial for building trust and gaining acceptance from medical professionals.
*   **Security:** We leverage Frappe's robust, role-based access control (RBAC) to ensure that only authorized users can access sensitive patient data. All medical images and patient data are stored as private files within the Frappe framework.
