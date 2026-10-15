import os
import time

import httpx
from dotenv import load_dotenv


load_dotenv()


COURIER_API_BASE_URL = os.getenv(
    "COURIER_API_BASE_URL",
    "http://127.0.0.1:8001",
)


class CourierServiceError(Exception):
    pass


class ShipmentNotFoundError(Exception):
    pass


def get_shipment(
    order_number: str,
    max_attempts: int = 3,
) -> dict:

    url = (
        f"{COURIER_API_BASE_URL}"
        f"/shipments/{order_number}"
    )

    timeout = httpx.Timeout(
        3.0
    )


    for attempt in range(
        1,
        max_attempts + 1,
    ):

        try:

            print(
                f"Courier API attempt "
                f"{attempt}/{max_attempts}"
            )

            response = httpx.get(
                url,
                timeout=timeout,
            )


            if response.status_code == 404:

                raise ShipmentNotFoundError(
                    f"No shipment found for "
                    f"{order_number}"
                )


            if response.status_code >= 500:

                raise CourierServiceError(
                    "Courier service returned "
                    f"HTTP {response.status_code}"
                )


            response.raise_for_status()

            return response.json()


        except ShipmentNotFoundError:

            # A 404 is a genuine business result.
            # Retrying will not magically create
            # the shipment, so we fail immediately.

            raise


        except (
            httpx.TimeoutException,
            httpx.NetworkError,
            CourierServiceError,
        ) as error:

            if attempt == max_attempts:

                raise CourierServiceError(
                    "Courier service unavailable "
                    f"after {max_attempts} attempts. "
                    f"Last error: {error}"
                ) from error


            wait_seconds = (
                0.5 * attempt
            )

            print(
                "Temporary courier failure. "
                f"Retrying in "
                f"{wait_seconds:.1f} seconds..."
            )

            time.sleep(
                wait_seconds
            )


        except httpx.HTTPStatusError as error:

            raise CourierServiceError(
                "Unexpected courier API "
                f"response: "
                f"{error.response.status_code}"
            ) from error


    raise CourierServiceError(
        "Courier request failed."
    )