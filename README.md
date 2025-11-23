# OpenWeatherMap One Call Home Assistant Integration

This is a custom Home Assistant integration for the OpenWeatherMap One Call API 3.0. It provides access to a wider range of weather data compared to the default OpenWeatherMap integration, including current weather, daily forecasts, and weather alerts.

## Features

*   **Comprehensive Weather Data:** Access to current weather conditions, daily forecasts (up to 8 days), and weather alerts from the OpenWeatherMap One Call API 3.0.
*   **Configurable Update Interval:** The integration intelligently calculates the data update interval based on your OpenWeatherMap API subscription's maximum daily requests, ensuring optimal API usage.
*   **HACS Compatible:** Easily install and manage this integration via Home Assistant Community Store (HACS).

## Installation

### Via HACS (Recommended)

1.  **Add Custom Repository:**
    *   Open Home Assistant.
    *   Go to `HACS` -> `Integrations`.
    *   Click on the three dots in the top right corner and select `Custom repositories`.
    *   Enter the URL of this GitHub repository (`https://github.com/Lomion-tm/ha-openweather-one-call`) and select `Integration` as the category.
    *   Click `ADD`.
2.  **Install Integration:**
    *   Search for "OpenWeatherMap One Call" in HACS and click on it.
    *   Click `INSTALL` and then `DOWNLOAD`.
    *   Restart Home Assistant.

### Manual Installation

1.  **Copy Files:**
    *   Download the contents of this repository.
    *   Copy the `custom_components/openweather_one_call` folder into your Home Assistant's `custom_components` directory.
    *   Your configuration directory is typically located at `/config` or `/usr/share/hassio/homeassistant`.
    *   The path should look like: `<config_directory>/custom_components/openweather_one_call/...`
2.  **Restart Home Assistant:**
    *   Restart your Home Assistant instance to load the new integration.

## Configuration

1.  **Add Integration:**
    *   Go to `Settings` -> `Devices & Services` -> `Integrations`.
    *   Click `ADD INTEGRATION`.
    *   Search for "OpenWeatherMap One Call".
    *   Follow the on-screen prompts to enter your OpenWeatherMap API Key, desired latitude and longitude, a name for the location, and your maximum daily API requests.
2.  **API Key:** Obtain your API Key from your [OpenWeatherMap account page](https://home.openweathermap.org/api_keys).
3.  **Location:** Enter the latitude and longitude for the location you want to monitor.
4.  **Maximum Daily Requests:** Set the maximum number of daily API calls allowed by your OpenWeatherMap subscription. The integration will automatically adjust the update interval to stay within this limit, with a minimum interval of 10 minutes (as per OpenWeatherMap API recommendations).

## Entities

The integration will create various sensor and binary sensor entities based on the data available from the OpenWeatherMap One Call API.

### Sensor Entities (Examples)

*   `sensor.your_location_temperature`
*   `sensor.your_location_feels_like`
*   `sensor.your_location_humidity`
*   `sensor.your_location_wind_speed`
*   `sensor.your_location_daily_temperature_day`
*   `sensor.your_location_daily_probability_of_precipitation`

### Binary Sensor Entities (Examples)

*   `binary_sensor.your_location_weather_alerts_active`

## Development

To contribute or further develop this integration:

1.  Clone this repository.
2.  Ensure you have a development environment set up for Home Assistant custom components.
3.  Install necessary dependencies (`aiohttp`).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
