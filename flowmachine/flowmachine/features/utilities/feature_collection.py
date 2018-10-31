# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Class definition for FeatureCollection, this is a group of
joined features.
"""
from ...core import Query


class FeatureCollection(Query):
    """
    Joined set of features. Takes a set of features and creates
    one wide dataset about these features. Most often used to gather
    subscriber metrics into one dataframe, for instance to pass to a machine
    learning pipeline.

    Parameters
    ----------
    metrics : list of Query type objects
        A list (or other iterable) of objects which derive
        from the flowmachine.Query base class.
    dropna : bool
        Keeps rows in which a subscriber has some but not 
        all of the features. 

    Examples
    --------
    There are two alternative constructors to this class. The first
    is more general, it takes a list of query instances.
    
    >>> start, stop = '2016-01-01', '2016-01-03'
    >>> metrics = [RadiusOfGyration(start, stop),
                   NocturnalCalls(start, stop),
                   SubscriberDegree(start, stop)]

    >>> fc = FeatureCollection(metrics)
    >>> fc.head()
       subscriber            |rog_radiusofgyration_0|percentage_nocturnal_nocturnalcalls_1|degree_subscriberdegree_2
        ----------------|----------------------|-------------------------------------|-------------------
        038OVABN11Ak4W5P|162.003039769672      |28.571428571428573                   |2
        09NrjaNNvDanD8pk|191.563707606684      |58.333333333333336                   |2
        0ayZGYEQrqYlKw6g|253.993944670455      |27.272727272727273                   |2
        0DB8zw67E9mZAPK2|230.161989941767      |18.181818181818183                   |2
        0Gl95NRLjW2aw8pW|127.234294155594      |44.44444444444444                    |2

    Sometimes a subscriber may only have a value associated to some of the 
    features in the collection. The default behaviour of this class is only 
    to return rows that have values for all the features. To override this 
    behaviour we can do the following;

    >>> fc = FeatureCollection(metrics, dropna=False)
    >>> fc.head()
        subscriber      |rog_radiusofgyration_0|percentage_nocturnal_nocturnalcalls_1|degree_subscriberdegree_2
        ----------------|----------------------|-------------------------------------|-------------------
        038OVABN11Ak4W5P|162.003039769672      |28.571428571428573                   |2
        09NrjaNNvDanD8pk|Nan                   |58.333333333333336                   |2
        0ayZGYEQrqYlKw6g|253.993944670455      |Nan                                  |2
        0DB8zw67E9mZAPK2|230.161989941767      |18.181818181818183                   |2
        0Gl95NRLjW2aw8pW|127.234294155594      |44.44444444444444                    |2


    An alternative, and easier way, to get the following is to do:

    >>> start, stop = '2016-01-01', '2016-01-03'
    >>> metrics = [RadiusOfGyration,
                   NocturnalCalls,
                   SubscriberDegree]

    >>> fc = FeatureCollection.from_list_of_classes(metrics, start, stop)

    But this requires that you want the same arguments for each class 
    (and are happy with the defaults).

    Notes
    -----
    Each column has the name of the class appended to it to distinguish
    it from other potential inputs, and an integer. This is because the column
    names must be unique, and it is possible to use the same metric 
    multiple times but with different parameters.

    """

    def __init__(self, metrics, dropna=True):

        self.joined_metrics = self.__join_queries(metrics, dropna)

        super().__init__()

    @classmethod
    def from_list_of_classes(cls, classes, *args, **kwargs):
        """
        From uninstantiated classes with common arguments.
        """

        metrics = [c(*args, **kwargs) for c in classes]
        return cls(metrics)

    # Private method that joins multiple queries together
    # and returns a joined query.
    @staticmethod
    def __join_queries(queries, dropna):

        # We want to handle the first case as a special case, as we
        # need to give the left object a name on the first join, but
        # not in any subsequent joins.
        col = queries[0].column_names[0]
        left_append = "_" + queries[0].__class__.__name__ + "_0"
        right_append = "_" + queries[1].__class__.__name__ + "_1"
        how = "inner" if dropna else "full outer"
        running_join = queries[0].join(
            queries[1],
            on_left=col,
            left_append=left_append,
            right_append=right_append,
            how=how,
        )

        for i, q in enumerate(queries[2:]):
            col = q.column_names[0]
            append = "_" + q.__class__.__name__ + "_{}".format(i + 2)
            running_join = running_join.join(
                q, on_left=col, right_append=append, how=how
            )
            # Trigger memoization
            _ = q.md5
            _ = running_join.md5
            _ = running_join.column_names

        return running_join

    def _make_query(self):
        return self.joined_metrics.get_query()
