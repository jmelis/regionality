.PHONY: generate-configs test clean help
OUTPUT_DIR ?= configs

# Default target
all: generate-configs

# Generate cluster configurations (configmaps and values files)
generate-configs: clean
	@echo "Generating cluster configurations..."
	cd tools/config-generator && uv run python3 generate_configs.py ../../$(OUTPUT_DIR)
	@echo "✅ Configuration generation complete!"
	@echo "📁 ConfigMaps generated in: $(OUTPUT_DIR)/configmaps/"
	@echo "📁 Values files generated in: $(OUTPUT_DIR)/values/"

# Run tests
test:
	@echo "Running tests..."
	cd tools/config-generator && uv run python3 test_generate_configs.py ../../$(OUTPUT_DIR)
	@echo "✅ All tests passed!"

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	rm -rf $(OUTPUT_DIR)/
	@echo "✅ Clean complete!"

# Show help
help:
	@echo "Available targets:"
	@echo "  generate-configs  Generate cluster configurations (default)"
	@echo "  test             Run the test suite"
	@echo "  clean            Remove generated files"
	@echo "  help             Show this help message"
