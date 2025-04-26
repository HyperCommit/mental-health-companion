# Coding Rules and Best Practices

## General Rules
- Follow Python PEP 8 style guidelines for all Python code.
- Use meaningful and descriptive names for variables, functions, and classes.
- Write modular, reusable, and testable code.
- Include type annotations for all function parameters and return values.
- Add docstrings for all public functions, classes, and modules.

## Python Design Patterns
- Use appropriate design patterns for maintainable and scalable code:
  - **Factory Method** for dynamic object creation.
  - **Singleton** for ensuring a single instance of a class.
  - **Builder** for constructing complex objects step by step.
  - **Observer** for event-driven systems.
  - **Strategy** for runtime behavior changes.
- Implement error handling with specific exceptions and custom exception classes.

## Markdown Documentation Rules
- Use headers (`#`, `##`, `###`) to structure documents.
- Keep line length under 120 characters for readability.
- Use code blocks with language specifiers for syntax highlighting.
- Add alt text to images for accessibility.
- Include a table of contents for documents longer than three sections.

## Azure-Specific Rules
- **@azure Rule**: Use Azure Best Practices for all Azure-related code and operations.
- **@azure Rule**: When generating Azure-related code or running Azure commands, invoke the `azure_development-get_best_practices` tool if available.
- Use Azure SDKs for interacting with Azure services.
- Implement retry patterns with exponential backoff for Azure service calls.
- Use Azure Identity for authentication and avoid hardcoding credentials.
- Add proper telemetry and logging for Azure services using Application Insights.
