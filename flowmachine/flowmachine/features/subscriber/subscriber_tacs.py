# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# -*- coding: utf-8 -*-
"""
Features that represent TACs (unique phone model identifiers), and handsets associated with
a subscriber.



"""
import warnings
from typing import List

from ..utilities.sets import EventsTablesUnion
from .metaclasses import SubscriberFeature
from ...core import Table


class SubscriberTACs(SubscriberFeature):
    """
    Class representing all the TACs for which a subscriber has been associated.

    Parameters
    ----------
    start, stop : str
         iso-format start and stop datetimes
    hours : 2-tuple of floats, default 'all'
        Restrict the analysis to only a certain set
        of hours within each day.
    table : str, default 'all'
    subscriber_identifier : {'msisdn', 'imei'}, default 'msisdn'
        Either msisdn, or imei, the column that identifies the subscriber.
    subscriber_subset : str, list, flowmachine.core.Query, flowmachine.core.Table, default None
        If provided, string or list of string which are msisdn or imeis to limit
        results to; or, a query or table which has a column with a name matching
        subscriber_identifier (typically, msisdn), to limit results to.
    kwargs :
        Passed to flowmachine.EventsTablesUnion


    Examples
    -------------

    >>> subscriber_tacs = SubscriberTACs('2016-01-01 13:30:30',
                               '2016-01-02 16:25:00')
    >>> subscriber_tacs.head()
                subscriber                      time         tac
    0     1vGR8kp342yxEpwY 2016-01-01 13:31:06+00:00  85151913.0
    1     QPdr2B94VaEzZgoW 2016-01-01 13:31:06+00:00  15314569.0
    2     LjDxeZEREElG7m0r 2016-01-01 13:32:21+00:00  92380772.0
                            .
                            .
                            .
    """

    def __init__(
        self,
        start,
        stop,
        hours="all",
        table="all",
        subscriber_identifier="msisdn",
        **kwargs,
    ):
        """

        """

        self.start = start
        self.stop = stop
        self.hours = hours
        self.table = table
        self.subscriber_identifier = subscriber_identifier
        self.tbl = EventsTablesUnion(
            start,
            stop,
            [subscriber_identifier, "tac", "datetime"],
            tables=table,
            subscriber_identifier=self.subscriber_identifier,
            **kwargs,
        )

        super().__init__()

    @property
    def column_names(self) -> List[str]:
        return ["subscriber", "time", "tac"]

    def _make_query(self):
        return f"""
                SELECT subscriber, datetime AS time, tac
                FROM ({self.tbl.get_query()}) e
                WHERE tac IS NOT NULL ORDER BY datetime"""


class SubscriberTAC(SubscriberFeature):
    """
    Class representing a single TAC associated to the subscriber.

    Parameters
    ----------
    start, stop : str
         iso-format start and stop datetimes
    hours : 2-tuple of floats, default 'all'
        Restrict the analysis to only a certain set
        of hours within each day.
    table : str, default 'all'
    subscriber_identifier : str, default 'msisdn'
        The focus of the analysis, usually either
        'msisdn', 'imei'
    method : {'most-common', 'last'}
        Method for choosing a TAC to associate.
    kwargs :
        Passed to flowmachine.EventsTablesUnion


    Examples
    --------

    >>> subscriber_tacs = SubscriberTAC('2016-01-01', '2016-01-07')
    >>> subscriber_tacs.head()
             subscriber         tac
    0  038OVABN11Ak4W5P  18867440.0
    1  09NrjaNNvDanD8pk  21572046.0
    2  0ayZGYEQrqYlKw6g  81963365.0
    3  0DB8zw67E9mZAPK2  92380772.0
    4  0Gl95NRLjW2aw8pW  77510543.0
                            .
                            .
                            .

    Notes
    -----

    Be aware that when using a imei as a subscriber identifier, than one imei
    is always associated to a _single_ TAC.
    """

    def __init__(
        self,
        start,
        stop,
        hours="all",
        table="all",
        subscriber_identifier="msisdn",
        method="most-common",
        **kwargs,
    ):
        """

        """

        if subscriber_identifier == "imei":
            warnings.warn("IMEI has a one to one mapping to TAC number.")

        self.start = start
        self.stop = stop
        self.hours = hours
        self.table = table
        self.subscriber_identifier = subscriber_identifier
        self.subscriber_tacs = SubscriberTACs(
            start,
            stop,
            hours=hours,
            table=table,
            subscriber_identifier=subscriber_identifier,
            **kwargs,
        )
        self.method = method
        if self.method not in ("most-common", "last"):
            raise ValueError("{} is not a valid method.".format(method))
        super().__init__()

    @property
    def column_names(self) -> List[str]:
        return ["subscriber", "tac"]

    def _make_query(self):
        if self.method == "most-common":
            query = """
                    SELECT t.subscriber as subscriber, pg_catalog.mode() WITHIN GROUP(ORDER BY tac) as tac
                    FROM ({}) t
                    GROUP BY t.subscriber""".format(
                self.subscriber_tacs.get_query()
            )
        elif self.method == "last":
            query = """
                    SELECT DISTINCT ON(t.subscriber) t.subscriber as subscriber, tac
                    FROM ({}) t 
                    ORDER BY t.subscriber, time DESC
            """.format(
                self.subscriber_tacs.get_query()
            )
        return query


class SubscriberHandsets(SubscriberFeature):
    """
    Class representing all the handsets for which a subscriber has been associated.

    Parameters
    ----------
    start, stop : str
         iso-format start and stop datetimes
    hours : 2-tuple of floats, default 'all'
        Restrict the analysis to only a certain set
        of hours within each day.
    table : str, default 'all'
    subscriber_identifier : str, default 'msisdn'
        The focus of the analysis, usually either
        'msisdn', 'imei'
    kwargs :
        Passed to flowmachine.EventsTablesUnion


    Examples
    -------------

    >>> subscriber_handsets = SubscriberHandsets('2016-01-01 13:30:30',
                               '2016-01-02 16:25:00')
    >>> subscriber_handsets.get_dataframe()
              tac        subscriber                      time    brand  model width   ...    j2me_midp_20 j2me_midp_21 j2me_cldc_10 j2me_cldc_11 j2me_cldc_20 hnd_type
    0  85151913.0  1vGR8kp342yxEpwY 2016-01-01 13:31:06+00:00     Sony  KQ-99  None   ...            None         None         None         None         None  Feature
    1  15314569.0  QPdr2B94VaEzZgoW 2016-01-01 13:31:06+00:00     Oppo  UT-18  None   ...            None         None         None         None         None    Smart
    2  92380772.0  LjDxeZEREElG7m0r 2016-01-01 13:32:21+00:00     Oppo  GK-00  None   ...            None         None         None         None         None  Feature
    3  99503609.0  Kabe7EppYbMEj6O3 2016-01-01 13:32:21+00:00  Samsung  NN-71  None   ...            None         None         None         None         None    Smart
    4  16875116.0  gWPl7QBD8VnEyX8K 2016-01-01 13:34:41+00:00     Sony  JH-73  None   ...            None         None         None         None         None    Smart

                            .
                            .
                            .
    """

    def __init__(
        self,
        start,
        stop,
        hours="all",
        table="all",
        subscriber_identifier="msisdn",
        **kwargs,
    ):
        """

        """

        self.start = start
        self.stop = stop
        self.hours = hours
        self.table = table
        self.subscriber_identifier = subscriber_identifier
        self.subscriber_tacs = SubscriberTACs(
            start,
            stop,
            hours=hours,
            table=table,
            subscriber_identifier=subscriber_identifier,
            **kwargs,
        )
        self.tacs = Table("infrastructure.tacs")
        self.joined = self.subscriber_tacs.join(self.tacs, "tac", "id", how="left")
        super().__init__()

    @property
    def column_names(self) -> List[str]:
        return self.joined.column_names

    def _make_query(self):
        return self.joined.get_query()


class SubscriberHandset(SubscriberFeature):
    """
    Class representing a single handset associated to the subscriber.

    Notes
    -----

    Be aware that when using a imei as a subscriber identifier, than one imei
    is always associated to a _single_ handset.

    Parameters
    ----------
    start, stop : str
         iso-format start and stop datetimes
    hours : 2-tuple of floats, default 'all'
        Restrict the analysis to only a certain set
        of hours within each day.
    table : str, default 'all'
    subscriber_identifier : str, default 'msisdn'
        The focus of the analysis, usually either
        'msisdn', 'imei'
    method : {'most-common', 'last'}
        Method for choosing a handset to associate.
    kwargs :
        Passed to flowmachine.EventsTablesUnion


    Examples
    -------------

    >>> subscriber_handsets = SubscriberHandset('2016-01-01', '2016-01-07')
    >>> subscriber_handsets.get_dataframe()
              tac        subscriber  brand  model width height depth   ...    j2me_midp_10 j2me_midp_20 j2me_midp_21 j2me_cldc_10 j2me_cldc_11 j2me_cldc_20 hnd_type
    0  18867440.0  038OVABN11Ak4W5P   Sony  TO-64  None   None  None   ...            None         None         None         None         None         None    Smart
    1  21572046.0  09NrjaNNvDanD8pk  Apple  WS-44  None   None  None   ...            None         None         None         None         None         None  Feature
    2  81963365.0  0ayZGYEQrqYlKw6g   Sony  YG-07  None   None  None   ...            None         None         None         None         None         None    Smart
    3  92380772.0  0DB8zw67E9mZAPK2   Oppo  GK-00  None   None  None   ...            None         None         None         None         None         None  Feature
    4  77510543.0  0Gl95NRLjW2aw8pW   Sony  KZ-03  None   None  None   ...            None         None         None         None         None         None  Feature

                            .
                            .
                            .
    """

    def __init__(
        self,
        start,
        stop,
        hours="all",
        table="all",
        subscriber_identifier="msisdn",
        method="most-common",
        **kwargs,
    ):
        """

        """

        self.start = start
        self.stop = stop
        self.hours = hours
        self.table = table
        self.subscriber_identifier = subscriber_identifier
        self.subscriber_tac = SubscriberTAC(
            start,
            stop,
            hours=hours,
            table=table,
            subscriber_identifier=subscriber_identifier,
            method=method,
            **kwargs,
        )
        self.method = method
        self.tacs = Table("infrastructure.tacs")
        self.joined = self.subscriber_tac.join(self.tacs, "tac", "id", how="left")
        super().__init__()

    @property
    def column_names(self) -> List[str]:
        return self.joined.column_names

    def _make_query(self):
        return self.joined.get_query()


class SubscriberPhoneType(SubscriberFeature):
    """
    Class representing which type of phone (Basic, Feature, or Smart) a subscriber
    is associated with.

    Parameters
    ----------
    start, stop : str
         iso-format start and stop datetimes
    hours : 2-tuple of floats, default 'all'
        Restrict the analysis to only a certain set
        of hours within each day.
    table : str, default 'all'
    subscriber_identifier : str, default 'msisdn'
        The focus of the analysis, usually either
        'msisdn', 'imei'
    method : {'most-common', 'last'}
        Method for choosing a handset to associate.
    kwargs :
        Passed to flowmachine.EventsTablesUnion


    Examples
    -------------

    >>> subscriber_smart = SubscriberPhoneType('2016-01-01', '2016-01-07')
    >>> subscriber_smart.get_dataframe()
             subscriber handset_type
    0  038OVABN11Ak4W5P        Smart
    1  09NrjaNNvDanD8pk      Feature
    2  0ayZGYEQrqYlKw6g      Feature
    3  0DB8zw67E9mZAPK2      Feature
    4  0Gl95NRLjW2aw8pW      Feature
                            .
                            .
                            .
    Notes
    ----

    For most-common, this query checks whether the subscriber most commonly uses
    a particular type of phone, rather than the type of their most commonly
    used phone.
    """

    def __init__(
        self,
        start,
        stop,
        hours="all",
        table="all",
        subscriber_identifier="msisdn",
        method="most-common",
        **kwargs,
    ):
        """

        """

        self.start = start
        self.stop = stop
        self.hours = hours
        self.table = table
        self.subscriber_identifier = subscriber_identifier
        if method == "most-common":
            self.subscriber_handsets = SubscriberHandsets(
                start,
                stop,
                hours=hours,
                table=table,
                subscriber_identifier=subscriber_identifier,
                **kwargs,
            )
        else:
            self.subscriber_handsets = SubscriberHandset(
                start,
                stop,
                hours=hours,
                table=table,
                subscriber_identifier=subscriber_identifier,
                method=method,
                **kwargs,
            )
        self.method = method
        super().__init__()

    @property
    def column_names(self) -> List[str]:
        return ["subscriber", "handset_type"]

    def _make_query(self):
        if self.method == "most-common":
            query = """
                    SELECT t.subscriber as subscriber, pg_catalog.mode() WITHIN GROUP(ORDER BY t.hnd_type) as handset_type
                    FROM ({}) t
                    GROUP BY t.subscriber""".format(
                self.subscriber_handsets.get_query()
            )
        elif self.method == "last":
            query = """
            SELECT t.subscriber as subscriber, t.hnd_type as handset_type FROM
            ({}) t
            """.format(
                self.subscriber_handsets.get_query()
            )
        return query
