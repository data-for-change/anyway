Widgets
=======

This document is meant to create a standard and documentation of different widget types.

Whenever the word "value" appears - it's the value after localization, if such localization is needed (For example,
integers and floats don't need localization)

Widget Types
------------

1. Table

Table API structure:
`widget["data"]["items"]` contains a list of dictionaries, each dictionary represents a row in the table.
`headers` contains column names.

```
{
    "name": <Widget Name>,
    "data": {
        "items": [
          {
            "column1": <column 1 value>,
            "column2": <column 2 value>,
            "column3": <column 3 value>,
          },
          {
            "column1": <column 1 value>,
            "column2": <column 2 value>,
            "column3": <column 3 value>,
          },
          {
            "column1": <column 1 value>,
            "column2": <column 2 value>,
            "column3": <column 3 value>,
          },
        ],
        "text": {
          "title": <title value>,
          "headers": {
            "column1": <column 1 header value>,
            "column2": <column 2 header value>
      }
    }
  },
    "meta": {
        type: "table"
    }
}
```

Example: A table with 2 rows - output of hebrew localization

```
{
  "name": some_table,
  "data": {
    "items": [
      {
        "accident_date": "09/06/19",
        "accident_type": "התנגשות חזית אל צד",
        "killed_count": 1,
        "severe_injured_count": 2,
        "light_injured_count": 5
      },
      {
        "accident_date": "27/06/17",
        "accident_type": "התנגשות חזית אל צד",
        "killed_count": 0,
        "severe_injured_count": 1,
        "light_injured_count": 4
      }
    ],
    "text": {
      "title": "תאונות חמורות במקטע צומת נחשון (הגבורה) - צומת חטיבה שבע",
      "headers": {
        "accident_date": "תאריך",
        "accident_type": "סוג תאונה",
        "killed_count": "הרוג",
        "severe_injured_count": "קשה",
        "light_injured_count": "קל"
      }
    }
  },
  "meta": {
        type: "table"
  }
}
```

2. Two Pie Charts
Comparing 2 Pie Charts - each with 2 categories. 
The first pie is larger in the UI, second is smaller. 
Pie no.1 containing data for the larger pie, pie no.2 containing the smaller pie.

```
{
    "name": <Widget Name>,
    "data": {
                "items": {
                           "larger_pie": 
                                        [
                                            {
                                                "category_name": <category name value>,
                                                "category_count": <category count value>,
                                            },
                                            {
                                                "category_name": <category name value>,
                                                "category_count": <category count value>,
                                            },
                                        ],
                           "smaller_pie": 
                                        [
                                            {
                                                "category_name": <category name value>,
                                                "category_count": <category count value>,
                                            },
                                            {
                                                "category_name": <category name value>,
                                                "category_count": <category count value>,
                                            },
                                        ],
                           },
                "text": {
                            "title": <title value>,
                            "headers": 
                                    {
                                        "larger_pie": <larger pie header value>,
                                        "smaller_pie": <smaller pie header value>,
                                    }
                        }
            },
    "meta": {
        type: "2_pie_charts"
    }
}
```

Example:

```
{
  "name": "head_on_collisions_comparison",
  "data": {
    "items": {
      "larger_pie": [
        {
          "category_name": "חזיתיות",
          "category_count": 3
        },
        {
          "category_name": "אחרות",
          "category_count": 1
        }
      ],
      "smaller_pie": [
        {
          "category_name": "חזיתיות",
          "category_count": 178
        },
        {
          "category_name": "אחרות",
          "category_count": 541
        }
      ]
    },
    "text": {
      "title": "תאונות קטלניות ע״פ סוג",
      "headers": {
        "larger_pie": "כביש 25 במקטע צומת הערבה - צומת דימונה",
        "smaller_pie": "בכבישים בין-עירוניים (ללא צמתים) בכל הארץ"
      }
    }
  },
  "meta": {
    type: "2_pie_charts"
  }
}
```

3. Bar Chart - each label represents a different color in the graph
Stacked vs Grouped - should be indicated in API in a 

```
{
    "name": <Widget Name>,
    "data": {
                "items": {
                            "label1":
                                    [
                                        {
                                            "category1_name": <category 1 name value>,
                                            "category1_value": <category 1 value>
                                        },
                                        {
                                            "category2_name": <category 2 name value>,
                                            "category2_value": <category 2 value>
                                        }
                                    ],
                            "label2":
                                    [
                                        {
                                            "category1_name": <category 1 name value>,
                                            "category1_value": <category 1 value>
                                        },
                                        {
                                            "category2_name": <category 2 name value>,
                                            "category2_value": <category 2 value>
                                        }
                                    ]
                        }

                "text": {
                            "title": <title value>,
                            "labels": {
                                            "label1": <label1 name value>,
                                            "label2": <label2 name value>,
                                       }
                        }
            }
    "meta": {
        type: <"stacked_bar" OR "grouped_bar">

    }
}
```

Example:

```
{
    "name": "accident_count_by_car_type",
    "data": {
                "items": {
                            "label1":
                                    [
                                        {
                                            "category1_name": "רכב פרטי",
                                            "category1_value": 76
                                        },
                                        {
                                            "category2_name": "אחר",
                                            "category2_value": 24
                                        }
                                    ],
                            "label2":
                                    [
                                        {
                                            "category1_name": "רכב פרטי",
                                            "category1_value": 50
                                        },
                                        {
                                            "category2_name": "אחר",
                                            "category2_value": 50
                                        }
                                    ],
                          },

                "text": {
                            "title": "השוואת אחוז הרכבים בתאונות במקטע צומת דימונה - צומת בית אשל לעומת ממוצע ארצי",
                            "labels": {
                                            "label1": "מקטע",
                                            "label2": "ממוצע ארצי",
                                       }
                        }
            }
    "meta": {
        type: "stacked_bar"
    }
}
```

5. Line Graph - Can be either simple line graph (one line) or multiple line graph
```
{
    "name": <Widget Name>,
    "data": {
                "items": {
                            "label1":
                                    [
                                        {
                                            "x": <x value>,
                                            "y": <y value>
                                        },
                                        {
                                            "x": <x value>,
                                            "y": <y value>
                                        },
                                        {
                                            "x": <x value>,
                                            "y": <y value>
                                        },
                                    ],
                            "label2":
                                    [
                                        {
                                            "x": <x value>,
                                            "y": <y value>
                                        },
                                        {
                                            "x": <x value>,
                                            "y": <y value>
                                        },
                                        {
                                            "x": <x value>,
                                            "y": <y value>
                                        },
                                    ]
                        }

                "text": {
                            "title": <title value>,
                            "headers": {
                                            "label1": <label1 name value>,
                                            "label2": <label2 name value>,
                                       }
                        }
            }
    "meta": {
        type: "line"

    }
}
```
