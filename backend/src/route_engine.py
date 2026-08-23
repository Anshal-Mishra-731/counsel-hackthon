import math
import heapq
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def haversine_km(a, b):
    """
    Calculate great-circle distance between two coordinates.
    """
    lat1, lon1 = a
    lat2, lon2 = b

    R = 6371.0

    p1 = math.radians(lat1)
    p2 = math.radians(lat2)

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    x = (
        math.sin(dlat / 2) ** 2
        + math.cos(p1)
        * math.cos(p2)
        * math.sin(dlon / 2) ** 2
    )

    return 2 * R * math.asin(math.sqrt(x))


def load_ports(
    path=None,
):
    """
    Load supplier/destination ports from CSV.

    Expected columns:

        country
        port
        lat
        lng
        node_id   <- optional but recommended

    Example:

        Saudi Arabia,Ras Tanura,26.64,50.16,ras_tanura
        India,Jamnagar,22.47,69.07,india_jamnagar
    """

    if path is None:
        path = DATA_DIR / "ports.csv"

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Port dataset not found: {path}"
        )

    df = pd.read_csv(path)

    required = {
        "country",
        "port",
        "lat",
        "lng",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            "ports.csv is missing required columns: "
            + ", ".join(sorted(missing))
        )

    df["country"] = (
        df["country"]
        .astype(str)
        .str.strip()
    )

    df["port"] = (
        df["port"]
        .astype(str)
        .str.strip()
    )

    df["lat"] = pd.to_numeric(
        df["lat"],
        errors="coerce",
    )

    df["lng"] = pd.to_numeric(
        df["lng"],
        errors="coerce",
    )

    if df[
        ["lat", "lng"]
    ].isna().any().any():

        raise ValueError(
            "ports.csv contains invalid lat/lng values"
        )

    return df


def find_source_port(
    country,
    ports,
):
    """
    Find the port associated with a supplier country.
    """

    matches = ports[
        ports["country"]
        .str.lower()
        ==
        country.strip().lower()
    ]

    if matches.empty:
        raise ValueError(
            f"No port found for supplier country: {country}"
        )

    return matches.iloc[0]


def find_destination_port(
    country,
    ports,
    port_name=None,
):
    """
    Find destination port.

    If port_name is provided, use it.
    Otherwise use the first India port in the dataset.
    """

    matches = ports[
        ports["country"]
        .str.lower()
        ==
        country.strip().lower()
    ]

    if matches.empty:
        raise ValueError(
            f"No destination port found for country: {country}"
        )

    if port_name:
        selected = matches[
            matches["port"]
            .str.lower()
            ==
            port_name.strip().lower()
        ]

        if selected.empty:
            raise ValueError(
                f"Destination port '{port_name}' "
                f"not found for {country}"
            )

        return selected.iloc[0]

    return matches.iloc[0]


def load_maritime_network(
    nodes_path=None,
    edges_path=None,
):
    """
    Load maritime graph.

    nodes CSV:

        node_id
        lat
        lng
        name
        type

    edges CSV:

        from_node
        to_node
        distance_km
        risk_score
    """

    if nodes_path is None:
        nodes_path = DATA_DIR / "maritime_nodes.csv"

    if edges_path is None:
        edges_path = DATA_DIR / "maritime_edges.csv"

    nodes_path = Path(nodes_path)
    edges_path = Path(edges_path)

    if not nodes_path.exists():
        raise FileNotFoundError(
            f"Maritime nodes dataset not found: {nodes_path}"
        )

    if not edges_path.exists():
        raise FileNotFoundError(
            f"Maritime edges dataset not found: {edges_path}"
        )

    nodes = pd.read_csv(nodes_path)
    edges = pd.read_csv(edges_path)

    required_nodes = {
        "node_id",
        "lat",
        "lng",
    }

    required_edges = {
        "from_node",
        "to_node",
        "distance_km",
    }

    missing_nodes = (
        required_nodes - set(nodes.columns)
    )

    missing_edges = (
        required_edges - set(edges.columns)
    )

    if missing_nodes:
        raise ValueError(
            "maritime_nodes.csv missing columns: "
            + ", ".join(sorted(missing_nodes))
        )

    if missing_edges:
        raise ValueError(
            "maritime_edges.csv missing columns: "
            + ", ".join(sorted(missing_edges))
        )

    return nodes, edges


def _build_graph(
    nodes,
    edges,
    risk_penalty=0.0,
):
    """
    Convert maritime edge dataframe into
    adjacency graph.

    Cost:

        distance × (1 + risk_penalty × risk/100)

    """

    coordinates = {}

    for _, row in nodes.iterrows():

        coordinates[
            str(row["node_id"])
        ] = (
            float(row["lat"]),
            float(row["lng"]),
        )

    graph = {}

    for _, row in edges.iterrows():

        a = str(row["from_node"])
        b = str(row["to_node"])

        distance = float(
            row["distance_km"]
        )

        risk = float(
            row.get(
                "risk_score",
                0,
            )
        )

        cost = (
            distance
            *
            (
                1
                +
                risk_penalty
                * risk
                / 100
            )
        )

        graph.setdefault(
            a,
            [],
        ).append(
            (
                b,
                cost,
            )
        )

        graph.setdefault(
            b,
            [],
        ).append(
            (
                a,
                cost,
            )
        )

    return graph, coordinates


def shortest_route(
    source_id,
    destination_id,
    nodes,
    edges,
    risk_penalty=0.0,
):
    """
    Dijkstra shortest/risk-adjusted route.
    """

    source_id = str(source_id)
    destination_id = str(destination_id)

    graph, coordinates = _build_graph(
        nodes,
        edges,
        risk_penalty,
    )

    if source_id not in coordinates:
        raise ValueError(
            f"Source maritime node '{source_id}' "
            "not found in maritime_nodes.csv"
        )

    if destination_id not in coordinates:
        raise ValueError(
            f"Destination maritime node '{destination_id}' "
            "not found in maritime_nodes.csv"
        )

    queue = [
        (0.0, source_id)
    ]

    distances = {
        source_id: 0.0
    }

    previous = {}

    while queue:

        cost, node = heapq.heappop(
            queue
        )

        if node == destination_id:
            break

        if cost > distances.get(
            node,
            float("inf"),
        ):
            continue

        for neighbour, edge_cost in graph.get(
            node,
            [],
        ):

            new_cost = (
                cost
                + edge_cost
            )

            if new_cost < distances.get(
                neighbour,
                float("inf"),
            ):

                distances[neighbour] = new_cost

                previous[neighbour] = node

                heapq.heappush(
                    queue,
                    (
                        new_cost,
                        neighbour,
                    ),
                )

    if destination_id not in distances:
        raise ValueError(
            f"No maritime route found between "
            f"{source_id} and {destination_id}"
        )

    path = []

    node = destination_id

    while node != source_id:

        path.append(node)

        if node not in previous:
            raise ValueError(
                "Route reconstruction failed"
            )

        node = previous[node]

    path.append(source_id)

    path.reverse()

    waypoints = [
        list(coordinates[node])
        for node in path
    ]

    return {
        "node_path": path,
        "cost": round(
            distances[destination_id],
            2,
        ),
        "waypoints": waypoints,
    }


def _nearest_maritime_node(
    lat,
    lng,
    nodes,
):
    """
    Find nearest maritime graph node to a port.

    This is used to connect the real port
    coordinates to the maritime network.
    """

    best_node = None
    best_distance = float("inf")

    for _, row in nodes.iterrows():

        node_point = (
            float(row["lat"]),
            float(row["lng"]),
        )

        distance = haversine_km(
            (lat, lng),
            node_point,
        )

        if distance < best_distance:

            best_distance = distance
            best_node = row

    if best_node is None:
        raise ValueError(
            "No maritime nodes available"
        )

    return (
        str(best_node["node_id"]),
        best_distance,
    )


def build_route(
    source_country,
    destination,
    risk_penalty=0.0,
):
    """
    Complete route calculation:

        supplier country
              ↓
        ports.csv
              ↓
        nearest maritime node
              ↓
        maritime graph
              ↓
        Dijkstra
              ↓
        India destination
    """

    ports = load_ports()

    nodes, edges = load_maritime_network()

    source_port = find_source_port(
        source_country,
        ports,
    )

    destination_port = find_destination_port(
        destination["name"],
        ports,
        destination.get("port"),
    )

    source_lat = float(
        source_port["lat"]
    )

    source_lng = float(
        source_port["lng"]
    )

    destination_lat = float(
        destination_port["lat"]
    )

    destination_lng = float(
        destination_port["lng"]
    )

    source_node = None
    destination_node = None

    # If ports.csv has explicit node_id,
    # prefer that over nearest-node matching.

    if "node_id" in ports.columns:

        source_node_value = (
            source_port.get("node_id")
        )

        destination_node_value = (
            destination_port.get("node_id")
        )

        if pd.notna(
            source_node_value
        ):

            source_node = str(
                source_node_value
            )

        if pd.notna(
            destination_node_value
        ):

            destination_node = str(
                destination_node_value
            )

    # Otherwise connect port to
    # nearest maritime graph node.

    if source_node is None:

        source_node, _ = (
            _nearest_maritime_node(
                source_lat,
                source_lng,
                nodes,
            )
        )

    if destination_node is None:

        destination_node, _ = (
            _nearest_maritime_node(
                destination_lat,
                destination_lng,
                nodes,
            )
        )

    route_result = shortest_route(
        source_node,
        destination_node,
        nodes,
        edges,
        risk_penalty=risk_penalty,
    )

    # Add actual port coordinates at
    # beginning/end so Leaflet starts
    # exactly at the port.

    graph_waypoints = route_result[
        "waypoints"
    ]

    waypoints = [
        [
            source_lat,
            source_lng,
        ]
    ]

    waypoints.extend(
        graph_waypoints
    )

    waypoints.append(
        [
            destination_lat,
            destination_lng,
        ]
    )

    return {
        "source_country":
            source_country,

        "source_port":
            str(source_port["port"]),

        "source_coordinates": [
            source_lat,
            source_lng,
        ],

        "destination_country":
            str(destination["name"]),

        "destination_port":
            str(destination_port["port"]),

        "destination_coordinates": [
            destination_lat,
            destination_lng,
        ],

        "source_node":
            source_node,

        "destination_node":
            destination_node,

        "node_path":
            route_result["node_path"],

        "waypoints":
            waypoints,

        "route_cost":
            route_result["cost"],

        "route_method":
            "Dijkstra risk-adjusted maritime network",
    }