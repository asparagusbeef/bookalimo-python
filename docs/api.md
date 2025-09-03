# Book-A-Limo API Documentation

This document provides a comprehensive overview of the Book-A-Limo API, detailing the available endpoints, request/response formats, and data models.

NOTE: This is here for internal reference as we develop the wrapper. It is not intended to be a public facing document.

## Table of Contents
- [Book-A-Limo API Documentation](#book-a-limo-api-documentation)
  - [Table of Contents](#table-of-contents)
  - [API Endpoints](#api-endpoints)
    - [List Reservations](#list-reservations)
    - [Get Reservation](#get-reservation)
    - [Get Prices](#get-prices)
    - [Set Reservation Details](#set-reservation-details)
    - [Book Reservation](#book-reservation)
    - [Edit Reservation](#edit-reservation)
      - [Cancellation](#cancellation)
  - [Data Models](#data-models)
    - [Account](#account)
    - [Address](#address)
    - [Airport](#airport)
    - [BreakdownItem](#breakdownitem)
    - [City](#city)
    - [Credentials](#credentials)
    - [CreditCard](#creditcard)
    - [EditableReservation](#editablereservation)
    - [Location](#location)
    - [Meet\&Greet](#meetgreet)
    - [MeetGreetAdditional](#meetgreetadditional)
    - [Passenger](#passenger)
    - [Price](#price)
    - [Reservation](#reservation)
    - [Reward](#reward)
    - [Stop](#stop)
  - [Questions for the API Author (Ivan)](#questions-for-the-api-author-ivan)

---

## API Endpoints

### List Reservations
Use this function to get a list of previously booked reservations or to validate credentials.

`POST https://www.bookalimo.com/web/api/booking/reservation/list/`

**Request**

*   **Headers**: `content-type: application/json`

*   **Parameters**:

| Name | Data type | Required | Remark |
| :--- | :--- | :--- | :--- |
| `credentials` | [Credentials](#credentials) | Yes | User or account credentials. |
| `isArchive` | bool | No | Default value is `false`. Set `true` to load archive reservations instead of upcoming. |

*   **Example Request Body**:
```json
{
   "credentials":{
      "id":"TA10007",
      "isCustomer":false,
      "passwordHash":"e784f281dc827fab59fd806cf01e68d872ba5b8bfa55c55bfdb937b5239f4a83"
   },
   "isArchive": false
}
```

**Response**

*   **Response Properties**:

| Name | Data type | Nullable | Remark |
| :--- | :--- | :--- | :--- |
| `success` | bool | No | If `true` - credentials are valid. |
| `reservations` | [Reservation](#reservation)[] | No | Array of reservations. Can be empty, so use the `success` property to detect if credentials are valid. |
| `error` | string | Yes | Error message if any. |

*   **Example Response Body**:
```json
{
    "success": true,
    "reservations": [
        {
            "confirmationNumber": "5452655",
            "isArchive": false,
            "localDateTime": "06/20/2021 07:25 PM",
            "easternDateTime": "06/20/2021 07:25 PM",
            "rateType": 0,
            "passengerName": "John Smith",
            "pickupType": 1,
            "pickup": "JFK:DL New York, NY, US",
            "dropoffType": 0,
            "dropoff": "ICS Book A Limo office, 53 East 34th Street, Manhattan, New York, NY, US",
            "carClass": "SD"
        }
    ]
}
```

### Get Reservation
Use this function to get full information about a reservation. The `reservation` object in the response can be used to make an edit request.

`POST https://www.bookalimo.com/web/api/booking/reservation/get/`

**Request**

*   **Headers**: `content-type: application/json`

*   **Parameters**:

| Name | Data type | Required | Remark |
| :--- | :--- | :--- | :--- |
| `credentials` | [Credentials](#credentials) | Yes | User or account credentials. |
| `confirmation` | string | Yes | Confirmation number of the reservation. |

*   **Example Request Body**:
```json
{
   "credentials":{
      "id":"TA10007",
      "isCustomer":false,
      "passwordHash":"e784f281dc827fab59fd806cf01e68d872ba5b8bfa55c55bfdb937b5239f4a83"
   },
   "confirmation": "5452773"
}
```

**Response**

*   **Response Properties**:

| Name | Data type | Nullable | Remark |
| :--- | :--- | :--- | :--- |
| `reservation` | [EditableReservation](#editablereservation) | No | Reservation information that can be edited. |
| `isEditable` | bool | No | Indicates if the reservation can be edited. |
| `status` | int | Yes | `null`: active, `0`: No Show, `1`: Canceled, `2`: Late Cancelled. |
| `isCancellationPending` | bool | No | Indicates if reservation cancellation is pending. |
| `carDescription` | string | Yes | Description of the selected car class. |
| `cancellationPolicy` | string | Yes | Cancellation policy for the reservation. |
| `pickupType` | int | No | `0`: Address, `1`: Airport, `2`: Train Station, `3`: Cruise. |
| `pickupDescription` | string | No | Pick up location description. |
| `dropoffType` | int | No | `0`: Address, `1`: Airport, `2`: Train Station, `3`: Cruise. |
| `dropoffDescription` | string | No | Drop-off location description. |
| `additionalServices` | string | Yes | Description of the additional services, if any. |
| `paymentMethod` | string | Yes | Description of the payment method(s). |
| `breakdown` | [BreakdownItem](#breakdownitem)[] | No | Array of breakdown items. |
| `passengerName` | string | Yes | Full name of the passenger. |
| `evoucherUrl` | string | Yes | URL of the e-voucher (if filled up). |
| `receiptUrl` | string | Yes | URL of the receipt (for archive reservations). |
| `pendingChanges` | string[][] | No | Array of pending changes, if any. |

*   **Example Response Body**:
```json
{
    "reservation": {
        "confirmation": "5452773",
        "isCancelRequest": false,
        "rateType": 0,
        "pickupDate": "06/19/2024",
        "pickupTime": "07:50 PM",
        "stops": [{"description": "Brooklyn Bridge", "isEnRoute": false}, {"description": "Empire State Building", "isEnRoute": true}],
        "carClassCode": "SD",
        "passengers": 2, "luggage": 3, "pets": 1, "boosters": 1, "carSeats": 1, "infants": 1
    },
    "isEditable": true, "isCancellationPending": false, "carDescription": "Sedan Lincoln, Cadillac Or Similar",
    "cancellationPolicy": "3 Hours Before Dispatch Time (Jobs Between 1Am And 7Am Are Dispatched Before 8 Pm)",
    "pickupType": 1, "pickupDescription": "JFK:UA New York, NY, US", "dropoffType": 0, "dropoffDescription": "53 East 34th Street, Manhattan, New York, NY, US",
    "additionalServices": "Pet; Car Seat; Booster; Infant", "paymentMethod": "4184********0355",
    "breakdown": [
        {"name": "Base Fare", "value": 74.00, "isGrand": false}, {"name": "Stops", "value": 58.50, "isGrand": false},
        {"name": "Sub Total", "value": 132.50, "isGrand": true}, {"name": "Pet", "value": 25.00, "isGrand": false},
        {"name": "Car Seat", "value": 25.00, "isGrand": false}, {"name": "Booster", "value": 25.00, "isGrand": false},
        {"name": "Infant", "value": 25.00, "isGrand": false}, {"name": "Gratuity (20%)", "value": 26.50, "isGrand": false},
        {"name": "Tolls", "value": 10.00, "isGrand": false}, {"name": "Total", "value": 269.00, "isGrand": true},
        {"name": "STC Fee (12.9%)", "value": 34.70, "isGrand": false}, {"name": "NYS Fund (3%)", "value": 9.11, "isGrand": false},
        {"name": "Grand Total", "value": 312.81, "isGrand": true}, {"name": "Amount Due", "value": 312.81, "isGrand": true}
    ],
    "passengerName": "John Smith",
    "pendingChanges": [["Pick up time", "06/19/2024 08:50 PM"]]
}
```

### Get Prices
`POST https://www.bookalimo.com/web/api/booking/price/`

**Request**

*   **Headers**: `content-type: application/json`

*   **Parameters**:

| Name | Data type | Required | Remark |
| :--- | :--- | :--- | :--- |
| `credentials` | [Credentials](#credentials) | Yes | User or account credentials. |
| `rateType` | int | Yes | `0`: , `1`: |
| `dateTime` | string | Yes | Required format is `MM/dd/yyyy hh:mm tt` |
| `pickup` | [Location](#location) | Yes | Pick up location. |
| `dropoff` | [Location](#location) | Yes | Drop-off location. |
| `hours` | byte | No | For hourly `rateType` only. |
| `passengers` | byte | Yes | Passengers quantity. |
| `luggage` | byte | Yes | Luggage quantity. |
| `stops` | [Stop](#stop)[] | No | Array of stops. |
| `account` | [Account](#account) | No | Travel agency or corporate account info. **Attention**: TAs must provide this to get commission. |
| `passenger` | [Passenger](#passenger) | No | Passenger info. |
| `rewards` | [Reward](#reward)[] | No | Array of reward accounts. |
| `carClassCode` | string | No | Use only if you are looking for a specific car class. Example: `SD`. |
| `pets` | byte | No | Pets quantity. |
| `carSeats` | byte | No | Car seats quantity. |
| `boosters` | byte | No | Boosters quantity. |
| `infants` | byte | No | Infants quantity. |
| `customerComment` | string | No | Customer comment. |

*   **Example Request Body**:
```json
{
   "credentials": { "id": "TA10007", "isCustomer": false, "passwordHash": "e784f281dc827fab59fd806cf01e68d872ba5b8bfa55c55bfdb937b5239f4a83" },
   "rateType":0, "dateTime":"09/05/2025 12:44 AM",
   "pickup":{
      "type":1,
      "airport":{ "iataCode": "JFK", "countryCode": "US", "stateCode": "NY", "airlineIataCode": "UA", "airlineIcaoCode": "UAL", "flightNumber": "UA1234", "terminal": "7", "arrivingFromCity": { "cityName": "Los Angeles", "countryCode": "US", "stateCode": "CA", "stateName": "California" } }
   },
   "dropoff":{
      "type":0,
      "address": { "googleGeocode": { "formatted_address" : "53 E 34th St, New York, NY 10016, USA", "...": "..." }, "district": "Manhattan", "streetName": "East 34th Street", "building": "53", "zip": "10016" }
   },
   "passengers":2, "luggage":3,
   "stops":[ { "description":"Brooklyn Bridge", "isEnRoute":false }, { "description":"Empire State Building", "isEnRoute":true } ],
   "account":{ "id":"TA10007" },
   "pets":1, "carSeats":1, "boosters":1, "infants":1
}
```

**Response**

*   **Response Properties**:

| Name | Data type | Nullable | Remark |
| :--- | :--- | :--- | :--- |
| `token` | string | No | Session token, use it in subsequent requests. |
| `prices` | [Price](#price)[] | No | Array of prices. |

*   **Example Response Body**:
```json
{
   "token":"NdAbNwEeYM",
   "prices":[
      {
         "carClass":"SD", "carDescription":"Sedan Lincoln, Cadillac Or Similar", "maxPassengers":3, "maxLuggage":3, "price":312.82, "priceDefault":334.21, "defaultMeetGreet":2,
         "meetGreets":[ { "id":2, "name":"Baggage Claim", "...": "..." }, { "id":3, "name":"Curb Side", "...": "..." } ],
         "image128":"https://www.bookalimo.com/cdn/images/car/42/128.png", "image256":"https://www.bookalimo.com/cdn/images/car/42/256.png", "image512":"https://www.bookalimo.com/cdn/images/car/42/512.png"
      },
      {
         "carClass":"SUV", "carDescription":"Suv 5-6 Passengers Or Similar", "maxPassengers":6, "maxLuggage":6, "price":427.36, "priceDefault":448.76, "defaultMeetGreet":2,
         "meetGreets":[ { "id":2, "name":"Baggage Claim", "...": "..." }, { "id":3, "name":"Curb Side", "...": "..." } ],
         "image128":"https://www.bookalimo.com/cdn/images/car/47/128.png", "image256":"https://www.bookalimo.com/cdn/images/car/47/256.png", "image512":"https://www.bookalimo.com/cdn/images/car/47/512.png"
      }
   ]
}
```

### Set Reservation Details
Use this function to provide reservation details. It can be called multiple times; only non-null values will be applied. The price may change based on the details provided.

`POST https://www.bookalimo.com/web/api/booking/details/`

**Request**

*   **Headers**: `content-type: application/json`

*   **Parameters**:
| Name | Data type | Required | Remark |
| :--- | :--- | :--- | :--- |
| `token` | string | Yes | Token returned by the `price` function. |
| `carClassCode` | string | No | Car class code from the list returned by the `price` function. |
| `pickup` | [Location](#location) | No | Use only if pick up location is different. Price can be affected. |
| `dropoff` | [Location](#location) | No | Use only if drop-off location is different. Price can be affected. |
| `stops` | [Stop](#stop)[] | No | Use only if stops are different. Price can be affected. |
| `account` | [Account](#account) | No | Use only if account details are different. |
| `passenger` | [Passenger](#passenger) | No | Use only if passenger details are different. |
| `rewards` | [Reward](#reward)[] | No | Use only if rewards are different. |
| `pets` | byte | No | `null`: don't change; `number`: set new quantity. Price can be affected. |
| `carSeats` | byte | No | `null`: don't change; `number`: set new quantity. Price can be affected. |
| `boosters` | byte | No | `null`: don't change; `number`: set new quantity. Price can be affected. |
| `infants` | byte | No | `null`: don't change; `number`: set new quantity. Price can be affected. |
| `customerComment` | string | No | Use only if the comment is different. |
| `taFee` | decimal | No | For Travel Agencies only. An additional fee in USD on top of commission. |

*   **Example Request Body**:
```json
{
    "token": "NdAbNwEeYM",
    "carClassCode": "SD",
    "pickup":{
      "type":1,
      "airport":{ "iataCode": "JFK", "countryCode": "US", "stateCode": "NY", "airlineIataCode": "UA", "flightNumber": "UA1234", "terminal": "7", "meetGreet": 3, "arrivingFromCity": { "cityName": "Los Angeles", "countryCode": "US", "stateCode": "CA" } }
    },
    "passenger": { "firstName": "John", "lastName": "Smith", "email": "john@example.com", "phone": "+19173334455" },
    "rewards": [ { "type": 0, "value": "123456789" } ],
    "customerComment": "Please have a rock music playlist"
}
```

**Response**

*   **Response Properties**:

| Name | Data type | Nullable | Remark |
| :--- | :--- | :--- | :--- |
| `price` | decimal | No | Full price of the reservation. |
| `breakdown` | [BreakdownItem](#breakdownitem)[] | No | Array of breakdown items. |

*   **Example Response Body**:
```json
{
   "price":312.81,
   "breakdown":[
      {"name":"Base Fare", "value":74.00, "isGrand":false},
      {"name":"Stops", "value":58.50, "isGrand":false},
      {"name":"Sub Total", "value":132.50, "isGrand":true},
      {"name":"Pet", "value":25.00, "isGrand":false},
      {"name":"Grand Total", "value":312.81, "isGrand":true},
      {"name":"Amount Due", "value":312.81, "isGrand":true}
   ]
}
```

### Book Reservation
This is the final step of booking, which requires payment information. **Attention**: The credit card will be automatically authorized on the production server.

`POST https://www.bookalimo.com/web/api/booking/book/`

**Request**

*   **Headers**: `content-type: application/json`

*   **Parameters**:

| Name | Data type | Required | Remark |
| :--- | :--- | :--- | :--- |
| `token` | string | Yes | Token returned by the `price` function. |
| `promo` | string | No | Promo code. |
| `method` | string | No* | For charge accounts, set to `charge` and ignore `creditCard`. |
| `creditCard` | [CreditCard](#creditcard) | No* | Credit card info. |
*\* Either `method` or `creditCard` must be provided.*

*   **Example Request Body**:

```json
{
    "token": "NdAbNwEeYM",
    "promo": null,
    "creditCard": {
        "number": "4184 7284 3916 0355",
        "cardHolder": "John Smith",
        "expiration": "01/28",
        "cvv": "123",
        "zip": "10000",
        "holderType": "3"
    }
}
```

**Response**

*   **Response Properties**:

| Name | Data type | Nullable | Remark |
| :--- | :--- | :--- | :--- |
| `reservationId` | string | No | Confirmation number. |

*   **Example Response Body**:

```json
{
   "reservationId":"5452773"
}
```

### Edit Reservation
Use this function to create an edit request. This will only work if `isEditable` is `true` (from [Get Reservation](#get-reservation)). The reservation will be updated after revision; pending changes can be seen in the `pendingChanges` property. **Warning**: Submitting multiple edit requests will result in only the last one being processed.

`POST https://www.bookalimo.com/web/api/booking/edit/`

**Request**

*   **Headers**: `content-type: application/json`
*   **Body**: Include an [EditableReservation](#editablereservation) object in the post body.

*   **Example Request Body**:
```json
{
   "credentials":{
      "id":"TA10007",
      "isCustomer":false,
      "passwordHash":"e784f281dc827fab59fd806cf01e68d872ba5b8bfa55c55bfdb937b5239f4a83"
   },
   "confirmation":"5452773",
   "isCancelRequest": false,
   "rateType":0,
   "pickupDate":"06/19/2024",
   "pickupTime":"08:50 PM",
   "stops":[
      {"description":"Brooklyn Bridge", "isEnRoute":false},
      {"description":"Empire State Building", "isEnRoute":true}
   ],
   "carClassCode":"SD",
   "passengers":2, "luggage":3, "pets":1, "boosters":1, "carSeats":1, "infants":1
}
```

**Response**

*   **Example Response Body**:
```json
{
    "success": true
}
```

#### Cancellation
Cancellation is a part of the Edit function. Set `isCancelRequest` to `true`.

*   **Example Cancellation Request Body**:
```json
{
   "credentials":{
      "id":"TA10007",
      "isCustomer":false,
      "passwordHash":"e784f281dc827fab59fd806cf01e68d872ba5b8bfa55c55bfdb937b5239f4a83"
   },
   "confirmation":"5452773",
   "isCancelRequest": true
}
```

*   **Example Response Body**:
```json
{
    "success": true
}
```

---

## Data Models

### Account
| Name | Data type | Required | Remark |
| :--- | :--- | :--- | :--- |
| `id` | string | Yes | Travel agency or corporate account number. |
| `department` | string | No | Account department. |
| `bookerFirstName` | string | No | First name of the booker. |
| `bookerLastName` | string | No | Last name of the booker. |
| `bookerEmail` | string | No | Email address of the booker. |
| `bookerPhone` | string | No | Phone number of the booker in E164 format. |

### Address
| Name | Data type | Required | Remark |
| :--- | :--- | :--- | :--- |
| `googleGeocode` | string | No* | **Recommended.** Raw response of Google Geocoding API. |
| `city` | [City](#city) | No* | **Not Recommended.** Use only if you can't provide `googleGeocode`. |
| `district` | string | No | City district name, e.g., `Manhattan`. |
| `neighbourhood` | string | No | City neighbourhood name, e.g., `Lower Manhattan`. |
| `placeName` | string | No* | Place name, e.g., `Empire State Building`. |
| `streetName` | string | No* | Street name only, e.g., `East 34th st.`. |
| `building` | string | No | Building number only, e.g., `53`. |
| `suite` | string | No | e.g., `5P`. |
| `zip` | string | No | e.g., `10016`. |
> [!NOTE]
> **Source Inconsistency**: The documentation states "*Either **googlePlaceId** OR city must be provided,*" but the corresponding field in the example is `googleGeocode`.
*\* Either `placeName` or `streetName` must be provided.*

### Airport
| Name | Data type | Required | Remark |
| :--- | :--- | :--- | :--- |
| `iataCode` | string | Yes | 3-letter IATA airport code. Example: `JFK`. |
| `countryCode` | string | No | [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) country code. |
| `stateCode` | string | No | State code (US only). Example: `CA`. |
| `airlineIataCode` | string | No | 2-letter [IATA](https://www.iata.org/en/publications/directories/code-search) airline code. Example: `UA`. |
| `airlineIcaoCode` | string | No | 3-letter [ICAO](https://www.icao.int/publications/DOC8585/Pages/default.aspx) airline code. Example: `UAL`. |
| `flightNumber` | string | No | Example: `UA1234`. |
| `terminal` | string | No | Example: `7`. |
| `arrivingFromCity` | [City](#city) | No | City from which the plane is arriving. |
| `meetGreet` | int | No | Leave empty on price request to see options. `0`: Other, `1`: FBO, `2`: Baggage Claim, `3`: Curb Side, `4`: Gate, `5`: International, `6`: Greeter Service. |
> [!WARNING]
> **Potentially Erroneous Note**: The source documentation includes the following footnotes under the Airport section, which appear to be a copy-paste error from the Address section.
> *   *\* Either googlePlaceId OR city must be provided.*
> *   *\* Either placeName OR streetName must be provided.*

### BreakdownItem
| Name | Data type | Nullable | Remark |
| :--- | :--- | :--- | :--- |
| `name` | string | No | Name of breakdown item. |
| `value` | decimal | No | Value of breakdown item. |
| `isGrand` | bool | No | Indicates if the item should be highlighted (e.g., totals). |

### City
| Name | Data type | Required | Remark |
| :--- | :--- | :--- | :--- |
| `cityName` | string | Yes | Example: `Los Angeles`. |
| `countryCode` | string | Yes | [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) standard. Example: `US`. |
| `stateCode` | string | No | State code (if any). Example: `CA`. |
| `stateName` | string | No | State name (if any). Example: `California`. |

### Credentials
| Name | Data type | Required | Remark |
| :--- | :--- | :--- | :--- |
| `id` | string | Yes | If `isCustomer` is `false`: TA/corp number. If `true`: customer email/phone (E164). |
| `isCustomer` | bool | No | `false`: sign in as TA/corp. `true`: sign in as customer. |
| `passwordHash` | string | Yes | `Sha256(Sha256(Password) + LowerCase(Id))` |

### CreditCard
| Name | Data type | Required | Remark |
| :--- | :--- | :--- | :--- |
| `number` | string | Yes | Credit card number. |
| `expiration` | string | Yes | Expiration date in `MM/YY` format. |
| `cvv` | string | Yes | Credit card security number. |
| `cardHolder` | string | Yes | Name on a card. |
| `zip` | string | No | ZIP code. |
| `holderType` | int | No | `0`: [unspecified], `1`: [unspecified] |

### EditableReservation
| Name | Data type | Nullable | Remark |
| :--- | :--- | :--- | :--- |
| `credentials` | [Credentials](#credentials) | Yes | Required for the edit request. |
| `confirmation` | string | No | Confirmation number of the reservation. |
| `isCancelRequest` | bool | No | Set `true` to cancel reservation. |
| `rateType` | int | Yes | `0`: P2P, `1`: Hourly, `2`: Daily, `3`: Tour, `4`: Round Trip, `5`: RT Half |
| `pickupDate` | string | Yes | Local date of the reservation. |
| `pickupTime` | string | Yes | Local time of the reservation. |
| `stops` | [Stop](#stop)[] | No | Array of stops. |
| `creditCard` | [CreditCard](#creditcard) | Yes | Credit card info. |
> [!NOTE]
> **Source Inconsistency**: The data model marks `creditCard` as required, but the provided **Edit Reservation** example request body omits it.
| `passengers` | byte | Yes | Passengers quantity. |
| `luggage` | byte | Yes | Luggage quantity. |
| `pets` | byte | Yes | Pets quantity. |
| `carSeats` | byte | Yes | Car seats quantity. |
| `boosters` | byte | Yes | Boosters quantity. |
| `infants` | byte | Yes | Infants quantity. |
| `other` | string | Yes | Other changes that are not listed. |

### Location
| Name | Data type | Required | Remark |
| :--- | :--- | :--- | :--- |
| `type` | int | Yes | `0`: Address, `1`: Airport |
| `address` | [Address](#address) | No* | Required if `type` is `0`. |
| `airport` | [Airport](#airport) | No* | Required if `type` is `1`. |
*\* Required if the corresponding type is selected.*

### Meet&Greet
| Name | Data type | Nullable | Remark |
| :--- | :--- | :--- | :--- |
| `id` | int | No | Option ID. |
| `name` | string | No | Option name. |
| `basePrice` | decimal | No | Base price of the option. |
| `instructions` | string | No | Passenger instruction for the option. |
| `additional` | [MeetGreetAdditional](#meetgreetadditional)[] | No | Array of additional charges. |
| `totalPrice` | decimal | No | Total price of the option without fees. |
| `fees` | decimal | No | Fees amount. |
| `reservationPrice` | decimal | No | Full reservation price if this option is selected. |

### MeetGreetAdditional
| Name | Data type | Nullable | Remark |
| :--- | :--- | :--- | :--- |
| `name` | string | No | Name of the additional service. |
| `price` | decimal | No | Price of the additional service. |

### Passenger
| Name | Data type | Required | Remark |
| :--- | :--- | :--- | :--- |
| `firstName` | string | Yes | First name of the passenger. |
| `lastName` | string | Yes | Last name of the passenger. |
| `email` | string | No | Email address of the passenger. |
| `phone` | string | Yes | Phone number of the passenger. |

### Price
| Name | Data type | Nullable | Remark |
| :--- | :--- | :--- | :--- |
| `carClass` | string | No | Car class code. |
| `carDescription` | string | No | Car class description. |
| `maxPassengers` | byte | No | Maximum passengers quantity. |
| `maxLuggage` | byte | No | Maximum luggage quantity. |
| `price` | decimal | No | Price WITHOUT Meet&Greet. |
| `priceDefault` | decimal | No | Price WITH default Meet&Greet option. |
| `image128` | string | No | URL of 128px width car image. |
| `image256` | string | No | URL of 256px width car image. |
| `image512` | string | No | URL of 512px width car image. |
| `defaultMeetGreet` | int | Yes | Default Meet&Greet option ID. |
| `meetGreets` | [Meet&Greet](#meetgreet)[] | No | Array of available Meet&Greet options (airport pickup only). |

### Reservation
| Name | Data type | Nullable | Remark |
| :--- | :--- | :--- | :--- |
| `confirmationNumber` | string | No | Confirmation number. |
| `isArchive` | bool | No | Indicates if the reservation is archived. |
| `localDateTime` | string | No | Local date & time of the reservation. |
| `easternDateTime` | string | Yes | Eastern date & time of the reservation. |
| `rateType` | int | No | `0`: P2P, `1`: Hourly, `2`: Daily, `3`: Tour, `4`: Round Trip, `5`: RT Half |
| `passengerName` | string | Yes | Full name of the passenger. |
| `pickupType` | int | No | `0`: Address, `1`: Airport, `2`: Train Station, `3`: Cruise |
| `pickup` | string | No | Pick up location description. |
| `dropoffType` | int | No | `0`: Address, `1`: Airport, `2`: Train Station, `3`: Cruise |
| `dropoff` | string | No | Drop-off location description. |
| `carClass` | string | No | Car class code. |
| `status` | int | Yes | `null`: Active, `0`: No Show, `1`: Canceled, `2`: Late Cancelled |

### Reward
| Name | Data type | Required | Remark |
| :--- | :--- | :--- | :--- |
| `type` | int | Yes | Available types: `0`: United MileagePlus |
| `value` | string | Yes | Reward account number. |

### Stop
| Name | Data type | Required | Remark |
| :--- | :--- | :--- | :--- |
| `description` | string | Yes | Can be an address, place name, comment, etc. |
| `isEnRoute` | bool | Yes | Indicates if the stop is en-route. |

---

## Questions for the API Author (Ivan)

Based on the initial documentation, the following points have inconsistencies or lack clarity. Could you please clarify them?

1. **`CreditCard.holderType`**: The meanings for `holderType` values `0` and `1` are not specified. What do these represent?
2. **`Address.googleGeocode` Field vs. Requirement**: The documentation requires "*Either `googlePlaceId` OR `city`*", but the field shown in examples and the data model is `googleGeocode`. Should we be using `googleGeocode` or `googlePlaceId`?
3. **Footnotes in `Airport` Model**: The `Airport` section includes footnotes ("*Either googlePlaceId OR city must be provided*") that seem to belong to the `Address` model. Can you confirm if this is a copy-paste error and these notes can be ignored for airports?
4. **`EditableReservation.creditCard` Requirement**: The `EditableReservation` model marks the `creditCard` field as required, but the example request for the "Edit Reservation" endpoint does not include it. Is this field conditionally required, or is the example/model incorrect?
5. **`Get Prices.rateType` Meanings**: The descriptions for `rateType` values `0` and `1` are blank. Can you provide the official meanings? (Inference suggests `0`=Point-to-Point, `1`=Hourly).
