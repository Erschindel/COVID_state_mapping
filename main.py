import datetime
import calendar

import pandas as pd
import numpy as np
import plotly.figure_factory as ff


class Map ():
    def __init__(self, state):
        self.state = state
        self.data = self.update_data()
        self.postal = self.get_postal()
        self.today = datetime.datetime.now()
        self.date_used = self.get_fips_and_covid()[0] # depending on time of day, not necessarily today's date
        self.fips = self.get_fips_and_covid()[1]
        self.newest_data = self.get_fips_and_covid()[2]
        self.prior_data = self.get_fips_and_covid()[3]

    def update_data(self):
        # get most recent data from Hopkins
        data = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv"
        df_full = pd.read_csv(data)
        # remove rows with missing data (ex. Mass is missing a FIPS row)
        return df_full[df_full["Province_State"] == self.state].dropna()

    def get_postal(self):
        # two-letter state codes, needed for plotting
        df = pd.read_csv("data/state_codes.csv")
        return df[df["State"] == self.state]["Postal"].iloc[0]

    def prior_day(self, day):
        # account for month/year changes
        # day is a datetime object
        if day.month == 1 and day.day == 1:
            return f"12/31/{int(day.strftime('%y')) - 1}"
        elif day.day == 1:
            yesterday = calendar.monthrange(day.year, day.month - 1)[1]
            return day.strftime(f"{day.month - 1}/{yesterday}/%y")
        else:
            return day.strftime(f"%m/{day.day - 1}/%y")

    def get_fips_and_covid(self):
        # data might not yet be updated that day, so try/except
        try:
            date_used = self.today.strftime("%m/%d/%y")
            newest_data = self.data[date_used].tolist() # bad date fails here
        except:
            date_used = self.prior_day(self.today)
            newest_data = self.data[date_used].tolist()

        date_prior = self.prior_day(datetime.datetime.strptime(date_used, "%m/%d/%y"))
        # check for duplicated columns, ex Michigan
        if all(self.data[date_used] == self.data[date_prior]):
            two_days_back = self.prior_day(datetime.datetime.strptime(date_prior, "%m/%d/%y"))
            prior_data = self.data[two_days_back].tolist()
        else:
            prior_data = self.data[date_prior].tolist()
        fips = self.data["FIPS"].tolist()

        return date_used, fips, newest_data, prior_data

    def plot_totals(self):
        colorlist = ["#ffffff","#fff3ef", "#ffe7de", "#ffdbcf", "#ffcfbf", "#ffc3af", "#ffb7a0", "#ffaa90", "#ff9e81", "#ff9172", "#ff8464", "#ff7655", "#ff6846", "#ff5837", "#ff4628", "#ff2f17", "#ff0000"]

        # totals are always positive, so safe to start bins from 0
        binning_endpoints = list(np.around(np.mgrid[0:max(self.newest_data):15j], decimals=0).astype(int))

        fig = ff.create_choropleth(values=self.newest_data,
                                    fips=self.fips,
                                    scope=[self.postal],
                                    binning_endpoints=binning_endpoints,
                                    show_hover=True,
                                    county_outline={'color': 'rgb(0,0,0)', 'width': 0.5},
                                    colorscale=colorlist,
                                    title=f"{self.state} confirmed COVID cases today"
                                    )
        fig.update_geos(fitbounds="locations")
        fig.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0},
            legend=dict(
                yanchor="bottom",
                y=0.01,
                xanchor="left",
                x=0.01
                )
            )

        fig.show()

    def plot_day_change(self):
        colorlist = ["#00ff00", "#58ff43", "#7dff64", "#99ff80", "#b1ff9a", "#c7ffb4", "#dbffcd", "#edffe6", "#ffffff", "#ffe7de", "#ffcfbf", "#ffb7a0", "#ff9e81", "#ff8464", "#ff6846", "#ff4628", "#ff0000"]

        values = np.array(self.newest_data) - np.array(self.prior_data)

        # Someday (hopefully), values will be more negative than positive. Need to prepare the bins accordingly
        if abs(min(values)) > abs(max(values)):
            binning_endpoints = list(np.around(np.mgrid[min(values):(min(values) * -1):15j], decimals=0).astype(int))
        else:
            binning_endpoints = list(np.around(np.mgrid[(max(values) * -1):max(values):15j], decimals=0).astype(int))

        fig = ff.create_choropleth(values=list(values),
                                    fips=self.fips,
                                    scope=[self.postal],
                                    binning_endpoints=binning_endpoints,
                                    show_hover=True,
                                    county_outline={'color': 'rgb(0,0,0)', 'width': 0.5},
                                    colorscale=colorlist,
                                    title=f"{self.state} confirmed COVID cases day change"
                                    )
        fig.update_geos(fitbounds="locations")
        fig.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0},
            legend=dict(
                yanchor="bottom",
                y=0.01,
                xanchor="left",
                x=0.01
                )
            )

        fig.show()


def run():
    user_state = input("Full state name: ")
    if user_state.title() == "District Of Columbia":
        to_plot = Map("District of Columbia")
    else:
        to_plot = Map(user_state.title())
    to_plot.plot_day_change()

    print(f"Latest data from {to_plot.date_used}")
    print("Day change of confirmed cases shown.")
    show_day_change = input("Show totals? (y/n): ")
    if show_day_change.lower() == "y":
        to_plot.plot_totals()
    else:
        return False

run()
