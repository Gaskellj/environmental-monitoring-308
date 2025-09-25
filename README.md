# environmental-monitoring-308

Arduino code and data manipulation/visualization for ESC-308 Environmental Monitoring at Union College. This project aims to assess water quality of a stream ("the groot") which runs through college grounds using an in-situ device containing an Arduino ESP32 and several sensors.

Sensors included within this project are:

1. Temperature sensor
2. pH sensor
3. Turbidity sensor
4. Total dissolved solids (TDS) sensor

## Data analysis and visualization

Arduino cloud offers a great visualization dashboard but limited opportunity to analyze and transform data. As such, we have chosen to use python given the number of available packages and prior data science work in the language. Arduino also offers an API which allows us to retrieve historical data from the cloud.

Data analysis can be found [here](python-data-analysis)

test git 3
