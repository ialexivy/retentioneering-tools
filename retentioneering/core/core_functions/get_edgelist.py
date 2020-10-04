import networkx as nx
import pandas as pd


def get_edgelist(self, *,
                 weight_col=None,
                 norm_type=None,
                 edge_attributes='edge_weight'):
    """
    Creates weighted table of the transitions between events.

    Parameters
    ----------
    weight_col: str (optional, default=None)
        Aggregation column for transitions weighting. To calculate weights
        as number of transion events use None. To calculate number
        of unique users passed through given transition 'user_id'.
         For any other aggreagtion, like number of sessions, pass the column name.

    norm_type: {None, 'full', 'node'} (optional, default=None)
        Type of normalization. If None return raw number of transtions
        or other selected aggregation column. 'full' - normalized over
        entire dataset. 'node' weight for edge A --> B normalized over
        user in A

    edge_attributes: str (optional, default 'edge_weight')
        Name for edge_weight columns

    Returns
    -------
    Dataframe with number of rows equal to all transitions with weight
    non-zero weight

    Return type
    -----------
    pd.DataFrame
    """
    if norm_type not in [None, 'full', 'node']:
        raise ValueError(f'unknown normalization type: {norm_type}')

    event_col = self.retention_config['event_col']
    time_col = self.retention_config['event_time_col']

    cols = [event_col, 'next_' + str(event_col)]

    data = self._get_shift().copy()

    # get aggregation:
    if weight_col is None:
        agg = (data
               .groupby(cols)[time_col]
               .count()
               .reset_index())
        agg.rename(columns={time_col: edge_attributes}, inplace=True)
    else:
        agg = (data
               .groupby(cols)[weight_col]
               .nunique()
               .reset_index())
        agg.rename(columns={weight_col: edge_attributes}, inplace=True)

    # apply normalization:
    if norm_type == 'full':
        if weight_col is None:
            agg[edge_attributes] /= agg[edge_attributes].sum()
        else:
            agg[edge_attributes] /= data[weight_col].nunique()

    if norm_type == 'node':
        if weight_col is None:
            event_transitions_counter = data.groupby(event_col)[cols[1]].count().to_dict()
            agg[edge_attributes] /= agg[cols[0]].map(event_transitions_counter)
        else:
            user_counter = data.groupby(cols[0])[weight_col].nunique().to_dict()
            agg[edge_attributes] /= agg[cols[0]].map(user_counter)

    return agg


def get_adjacency(self, *,
                  weight_col=None,
                  norm_type=None):
    """
    Creates edge graph in the matrix format. Row indeces are event_col values,
     from which the transition occured, and columns are events, to
    which the transition occured. The values are weights of the edges defined
    with weight_col and norm_type parameters.

    Parameters
    ----------
    weight_col: str (optional, default=None)
        Aggregation column for transitions weighting. To calculate weights
        as number of transion events use None. To calculate number
        of unique users passed through given transition 'user_id'.
         For any other aggreagtion, like number of sessions, pass the column name.

    norm_type: {None, 'full', 'node'} (optional, default=None)
        Type of normalization. If None return raw number of transtions
        or other selected aggregation column. 'full' - normalized over
        entire dataset. 'node' weight for edge A --> B normalized over
        user in A

    Returns
    -------
    Dataframe with number of columns and rows equal to unique number of
    event_col values.

    Return type
    -----------
    pd.DataFrame
    """
    agg = self.get_edgelist(weight_col=weight_col,
                            norm_type=norm_type)
    graph = nx.DiGraph()
    graph.add_weighted_edges_from(agg.values)
    return nx.to_pandas_adjacency(graph)