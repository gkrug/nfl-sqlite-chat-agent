## install.packages("nflfastR")   # if you don't already have it
library(nflfastR)
library(jsonlite)                  # toJSON()

# Read the schema file to get data types
schema_lines <- readLines("schema/schema_nflfastR_pbp.txt")
field_types <- list()

# Parse the schema file to extract field types
for (line in schema_lines) {
  if (grepl("^[a-zA-Z_][a-zA-Z0-9_]*:", line)) {
    parts <- strsplit(line, ":")[[1]]
    field_name <- trimws(parts[1])
    field_type <- trimws(parts[2])
    field_types[[field_name]] <- field_type
  }
}

# Convert field_descriptions to a list with both description and data type
field_descriptions_enhanced <- list()

for (i in 1:nrow(field_descriptions)) {
  field_name <- field_descriptions$Field[i]
  description <- field_descriptions$Description[i]
  data_type <- field_types[[field_name]] %||% "UNKNOWN"
  
  field_descriptions_enhanced[[field_name]] <- list(
    description = description,
    data_type = data_type
  )
}

# Write to JSON file in schema folder
write_json(field_descriptions_enhanced, "schema/field_descriptions.json", pretty = TRUE)
