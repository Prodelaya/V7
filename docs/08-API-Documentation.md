# API Documentation

## Contents

- [Request](#request)
  - [Parameters](#parameters)
  - [Filtering](#filtering)
  - [Restrictions](#restrictions)
  - [Examples of Requests](#examples-of-requests)
- [Result](#result)

---

## Request

**URL:** `https://api.apostasseguras.com/request`

**Method:** `GET`

### Headers

| Header          | Value              | Description                                      |
| --------------- | ------------------ | ------------------------------------------------ |
| `Authorization` | `Bearer api_token` | The token provided to you to access the API data |

---

## Parameters

### `product` (Mandatory)

```
product = surebets|middles|valuebets
```

Type of data requested.

### `source` (Mandatory)

```
source = bookies
```

Enumeration of bookmaker IDs for which data needs to be requested.

### `sport` (Mandatory)

```
sport = sports
```

Enumeration of sport IDs for which data needs to be requested.

### `limit`

```
limit = 25
```

A limit on the number of entries that can be obtained in one request. **Default:** `25`

### `cursor`

```
cursor = sort_by:id
```

Parameter to navigate through output results. Depending on whether we need to go forward or backward in the list, `sort_by` and `id` should be taken from the last or first records of the current output.

**Example:** For the output with `sort_by:id: 4609118910833099900`, `id:785141488` (assuming this is the ID of the last entry):

```
cursor=4609118910833099900:785141488
```

Adding this parameter to the request would mean the data output of the next page (if the ID was the last) or the previous page (if the ID was the first).

### `commissions`

```
commissions = betfair:5,betdaq:1.5
```

Commission values applied to the bets. In this example:
- **5%** commission applied to winnings on bets at Betfair
- **1.5%** commission for Betdaq

### `oddsFormat`

```
oddsFormat = eu|us|uk|my|hk|pr
```

Odds display format:

| Format | Description          |
| ------ | -------------------- |
| `eu`   | European (decimal)   |
| `us`   | American             |
| `uk`   | British (fractional) |
| `my`   | Malaysian            |
| `hk`   | Hong Kong            |
| `pr`   | Probability          |

### `outcomes`

```
outcomes = 2|3
```

Number of surebet outcomes: can be `2` or `3`. If the parameter is not specified or another value is specified, all possible variants will be displayed.

### `min_group_size`

```
min_group_size = 2
```

Minimum number of odds used for valuebets comparison and calculation: can be 2 and above. In JSON, the field is also displayed as `similar_size`, written after `id`.

### `group`

```
group = off
```

Shows all similar bets for the same event and line. **Default:** `group=type` (only one bet for an event is displayed).

---

## Filtering

All filters in the API function the same way as they do on the website. You can experiment with different filter settings on the website to determine the appropriate parameter values for your API requests.

### For Valuebets

#### Odds Filter

```
min-odds = 1.25
max-odds = 5
```

The value must be a number between **1** and **100,000** (inclusive).

#### Overvalue Filter

```
min-overvalue = 1.25
max-overvalue = 5
```

The value must be a number between **0** and **1,000,000** (inclusive).

> **Note:** Filter parameter values are specified as percentages. The API response, however, is provided as a regular number. To convert to percentage:
> 
> `Overvalue on website = (Overvalue from API - 1) * 100`

#### Probability Filter

```
min-probability = 100.2
max-probability = 1523.44
```

The value must be a number between **0** and **10,000** (inclusive).

### For Surebets

#### Profit Filter

```
min-profit = 10
max-profit = 1000
```

The value must be a number between **-5** and **100,000** (inclusive).

#### ROI Filter

```
min-roi = 10
max-roi = 100000
```

The value must be a number between **0** and **100,000,000** (inclusive).

#### Different Rules Filter

```
hide-different-rules = true
```

Excludes surebets with different sports rules where there is a possibility of losing all stakes involved.

### For Middles

#### Expected Value (EV) Filter

```
min-m-ev = 1
max-m-ev = 2
```

The value must be a number between **-100,000,000** and **100,000,000** (inclusive).

#### Odds Filter

```
min-m-k = 1.25
max-m-k = 5
```

The value must be a number between **0** and **100,000** (inclusive).

#### Loss When Missing Filter

```
min-m-bet = 1
max-m-bet = 10
```

The profit from winning only one bet or the loss if both bets lose. Value must be between **0** and **10,000** (inclusive).

#### Profit When Hitting Filter

```
min-m-win = 1
max-m-win = 10
```

The profit when winning two bets. Value must be between **0** and **10,000** (inclusive).

#### Probability Filter

```
min-probability = 100.2
max-probability = 1523.44
```

Estimated probability of middle hit. Value must be between **0** and **10,000** (inclusive).

### Filters Applicable to All API Requests

#### Event Start Time Filter

```
startOf = 1
endOf = 3
```

Filter by event start time, in hours. Combinations of days, hours, and minutes are also supported:

| Example            | Meaning                       |
| ------------------ | ----------------------------- |
| `startOf=PT15M`    | 15 minutes                    |
| `startOf=PT10H`    | 10 hours                      |
| `startOf=P2D`      | 2 days                        |
| `startOf=P2DT3H4M` | 2 days, 3 hours and 4 minutes |

> **Note:** The response is calculated based on UTC, regardless of the requester's time zone.

#### Age Filter

```
startAge = 1
endAge = 3
```

Filter by the surebet/valuebet/middle age. Uses the same format as the event start time.

#### Sort Order

```
order = field_desc
order = field_asc
```

Sets the sort order to ascending or descending. The field should be specified by one of the following parameters:

**Valuebets:**
- `default`
- `start_at`
- `probability`
- `value`
- `bk_probability`
- `bk_margin`

**Surebets:**
- `start_at`
- `created_at`
- `roi`

**Middles:**
- `start_at`
- `probability`
- `bet`
- `win`
- `ev`
- `k`

**Example:** `start_at_asc`

---

## Restrictions

⚠️ **No more than 2 requests per second.**

---

## Examples of Requests

### Basic Surebets Request

```
https://api.apostasseguras.com/request?product=surebets&source=1xbet|pinnaclesports|parimatch|marathonbet&sport=Basketball|Football|Tennis
```

### Surebets with Pagination

```
https://api.apostasseguras.com/request?product=surebets&source=1xbet|pinnaclesports|parimatch|marathonbet&sport=Basketball|Football|Tennis&limit=10&cursor=4609118910833099900:785141488
```

### Valuebets with Filters

```
https://api.apostasseguras.com/request?product=valuebets&source=betbonanza&sport=Basketball|Handball|&min-odds=1.0&max-odds=2.75&min-probability=0.01&max-probability=100&min-overvalue=1.0&max-overvalue=50&limit=500&group=off
```

### Quick Verification with curl

```bash
curl "https://api.apostasseguras.com/request?product=surebets&source=bet365|22bet|10bet|pokerstars&sport=Football|Volleyball" -H "Authorization: Bearer api_token"
```

---

## Result

### General Data

```json
{
    /* Time when the response was generated */
    "updated_at": 1684171109017,
    
    /* Whether it is possible to move forward through the list */
    "can_forward": true,
    
    /* Whether it is possible to move backward through the list */
    "can_backward": false,
    
    /* The number of records in the output */
    "limit": 25
}
```

---

### Bet Section

```json
{
    /* Bet ID */
    "id": 460444138,

    /* Tournament name as it appears on the bookmaker's website */
    "tournament": "Counter-Strike - BLAST Paris Major",

    /* Names of the participants as they appear on the bookmaker's website */
    "teams": ["Fnatic", "G2"],

    /* Overvalue of the bet in the range of 0 to 1. If 0, the value has not been calculated yet */
    "overvalue": 0,

    /* Probability of winning the bet in the range of 0 to 1. If 0, the value has not been calculated yet */
    "probability": 0,

    /* Odds value */
    "value": 4.56,

    /* Commission that the bookmaker takes from winnings. Given in the range of 0 to 1 */
    "commission": 0,

    /* Bookmaker's name */
    "bk": "parimatch",

    /* Match ID in the system */
    "event_id": 460159166,

    /* Kind of sport */
    "sport_id": "CounterStrike",
    
    /* Match start time as indicated on the bookmaker's website */
    "time": 1684157400000
}
```

#### Navigation Elements

There are three types of elements that describe navigation to a bet on the bookmaker's website:

| Element     | Description                               |
| ----------- | ----------------------------------------- |
| `event_nav` | Link to the match                         |
| `view_nav`  | Link to a specific market (betting group) |
| `stake_nav` | Link to a specific bet                    |

> **Note:** If only `event_nav` is present, it is used as a replacement for `view_nav` and `stake_nav`. If `event_nav` and `view_nav` are present but `stake_nav` is absent, `view_nav` serves as a replacement for `stake_nav`.

**Example `event_nav` structure:**

```json
{
    "event_nav": {
        /* An indication that the event link can be opened from an iframe */
        "direct": true,
        
        /* A list of links to be opened to get to the desired page */
        "links": [
            {
                /* Link name */
                "name": "main",

                /* HTTP request description */
                "link": {
                    /* Method of the HTTP request */
                    "method": "GET",

                    /* URL */
                    "url": "https://www.marathonbet.com/en/betting/Tennis/ITF/..."
                },
                
                /* List of link names to be opened with this one */
                "requirements": ["x"]
            },
            {
                /* Link name */
                "name": "x",

                /* HTTP request */
                "link": {
                    /* Method of the HTTP request */
                    "method": "POST",

                    /* URL */
                    "url": "https://www.marathonbet.com/en/betslip/add.htm",

                    /* Parameters of the HTTP request */
                    "params": {
                        "ch": "{...}", 
                        "url": "https://www.marathonbet.com/en/betting/..."
                    }
                }, 
                
                /* Maximum delay time between opening this link and the previous link */
                "maxDelay": 1500
            }
        ],
       
        /* Markers section - Data specific to each bookmaker */
        "markers": {
            "id": 2000863629,
            "inValue": 1.95,
            "bk": "marathonbet",
            "externalId": "441036222-126110536388",
            "eventId": "16407509"
        }
    }
}
```

> **Note:** The data in the markers section is specific to each bookmaker. You will need to check how to use this field if the code does not provide clear instructions for a particular bookmaker.

---

#### Bet Type Description

```json
{
    "type": {
        /* Condition corresponding to the bet type */
        "condition": "3.5", 
        
        /* Game situation type */
        "game": "regular", 
        
        /* Teams to which the bet applies */
        "base": "overall", 
        
        /* Type of countable results */
        "variety": "map", 
        
        /* Time period or part of the game */
        "period": "overtime", 
        
        /* Logical meaning of the bet */
        "type": "over", 
        
        /* Back/lay format (for betting exchanges) */
        "back": false,

        /* Negation of a bet */
        "no": false
    }
}
```

##### `game` Parameter Values

| Value                | Description                                          |
| -------------------- | ---------------------------------------------------- |
| `regular`            | Default game situation (e.g., bets on match outcome) |
| `first`              | First goal / corner kick / card, etc.                |
| `№ 2`                | Second goal / corner kick / card, etc.               |
| `last`               | Last goal / corner kick / card, etc.                 |
| `openingPartnership` | In cricket, the best opening partnership             |

##### `base` Parameter Values

| Value     | Description                                |
| --------- | ------------------------------------------ |
| `overall` | Home and/or away teams (e.g., match total) |
| `home`    | Home team                                  |
| `away`    | Away team                                  |
| `both`    | Both teams (e.g., both teams to score)     |

##### `type` Parameter Values

| Value      | Description                          |
| ---------- | ------------------------------------ |
| `win1`     | Victory of team 1                    |
| `win1RetX` | Victory of team 1 (draw returns bet) |
| `win2`     | Victory of team 2                    |
| `win2RetX` | Victory of team 2 (draw returns bet) |
| `draw`     | Draw                                 |
| `over`     | Over                                 |
| `under`    | Under                                |
| `yes`      | Happens                              |
| `no`       | Not happens                          |
| `odd`      | Odd                                  |
| `even`     | Even                                 |
| `ah1`      | Asian handicap of team 1             |
| `ah2`      | Asian handicap of team 2             |
| `eh1`      | European handicap of team 1          |
| `ehx`      | European handicap on draw            |
| `eh2`      | European handicap of team 2          |

> **Note:** Some bet types may imply additional conditions. For example, for `over`/`under` bets it is the total number, and for handicap bets it is the handicap value. These values will be included in the `condition` parameter.

---

### `/valuebets` Response

`records` - Enumeration of bets that are value bets.

---

### General Section for `/surebets` and `/middles`

```json
{
    /* Sorting code, according to which the result is returned */
    "sort_by": 4609118910833099900,

    /* Record (surebet/middle/valuebet) ID */
    "id": 785141488,

    /* Start time of the outcome event */
    "time": 1685835600000,

    /* Time of the surebet/middle creation */
    "created": 1684229420000,

    /* Number of surebets/middles related to the specified group of bets */
    "group_size": 2, 
    
    /* Collection of bets included in the surebet */
    "prongs": [...], 
    
    /* Optional: Indicates bets may be subject to different rules */
    "rd": [[0], [1], [1]]
}
```

---

### `/surebets` Response

```json
{
    /* Profitability of the surebet */
    "profit": 11.2812, 
    
    /* ROI (Return on Investment) of the surebet */
    "roi": 222.6584,
    
    /* List of flags for generative bets */
    "generatives": "0,2"
}
```

**Generatives Flag Values:**

| Flag | Description              |
| ---- | ------------------------ |
| `0`  | Regular bets             |
| `1`  | Probably generative bets |
| `2`  | Clearly generative bets  |

> A **generative bet** is a bet that generates a surebet.

---

### `/middles` Response

```json
{
    /* Possible loss if only one bet wins */
    "bet": 0.2452,
    
    /* Possible win if both bets win */
    "win": 0.5097,
    
    /* Probability of hitting a middle (when both bets win) */
    "probability": 0.3379,
    
    /* Middle odds (ratio of potential win to potential loss) */
    "overvalue": 1.0404,
    
    /* Mathematical expectation of the middle */
    "ev": 0.0099
}
```

> **Note:** The higher the `ev` value, the more advantageous the middle is.