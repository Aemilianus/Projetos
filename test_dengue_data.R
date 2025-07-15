# Test script for Dengue_SP_3550308.csv
# This demonstrates how to load and use the dengue data in RStudio

# Load the dengue data
dengue_data <- read.csv("data/Dengue_SP_3550308.csv")

# Display basic information about the dataset
print("Dengue Dataset Summary:")
print(paste("Rows:", nrow(dengue_data)))
print(paste("Columns:", ncol(dengue_data)))
print(paste("Municipality:", unique(dengue_data$municipality)))
print(paste("Geocode:", unique(dengue_data$geocode)))
print(paste("Year:", unique(dengue_data$year)))
print(paste("Weeks covered:", min(dengue_data$week), "to", max(dengue_data$week)))

# Display structure
str(dengue_data)

# Display first few rows
head(dengue_data)

# Basic statistics
summary(dengue_data$cases)