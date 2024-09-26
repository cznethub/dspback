cluster_by_id = {
    "2012073": "Bedrock Cluster",
    "2012264": "Bedrock Cluster",
    "2012357": "Bedrock Cluster",
    "2012316": "Bedrock Cluster",
    "2012353": "Bedrock Cluster",
    "2012227": "Bedrock Cluster",
    "2012408": "Bedrock Cluster",
    "2011439": "Big Data Cluster",
    "2012123": "Big Data Cluster",
    "2012188": "Big Data Cluster",
    "2011346": "Big Data Cluster",
    "2012080": "Big Data Cluster",
    "2012850": "CINET Cluster",
    "2012484": "Coastal Cluster",
    "2012322": "Coastal Cluster",
    "2012670": "Coastal Cluster",
    "2011941": "Coastal Cluster",
    "2012319": "Coastal Cluster",
    "2012475": "Drylands Cluster",
    "2012082": "Dust^2 Cluster",
    "2011910": "Dust^2 Cluster",
    "2012067": "Dust^2 Cluster",
    "2012093": "Dust^2 Cluster",
    "2012091": "Dust^2 Cluster",
    "2012669": "Dynamic Water Cluster",
    "2012821": "Dynamic Water Cluster",
    "2012796": "Dynamic Water Cluster",
    "2012730": "Dynamic Water Cluster",
    "2012310": "Dynamic Water Cluster",
    "2012878": "GeoMicroBio Cluster",
    "2012403": "GeoMicroBio Cluster",
    "2012633": "GeoMicroBio Cluster",
    "2217532": "GeoMicroBio Cluster",
    "2012409": "Urban Cluster",
    "2012616": "Urban Cluster",
    "2012336": "Urban Cluster",
    "2012107": "Urban Cluster",
    "2012340": "Urban Cluster",
    "2012313": "Urban Cluster",
    "2012344": "Urban Cluster",
    "2011617": "Urban Cluster",
    "2012593": "CZNet Hub",
    "2012893": "CZNet Hub",
    "2012748": "CZNet Hub",
}


def clusters(json_ld):
    resource_funding_ids = []
    if "funding" in json_ld:
        for funding in json_ld["funding"]:
            if "identifier" in funding:
                resource_funding_ids.append(funding["identifier"])

    _clusters = []
    for cluster_funding_id, cluster in cluster_by_id.items():
        for resource_funding_id in resource_funding_ids:
            if cluster_funding_id in resource_funding_id:  # '2012669' in 'EAR 2012669.'
                _clusters.append(cluster)

    return list(set(_clusters))


current_clusters = [
    "Bedrock Cluster",
    "Bedrock Cluster",
    "Big Data Cluster",
    "CINET Cluster",
    "Coastal Cluster",
    "Drylands Cluster",
    "Dust^2 Cluster",
    "Dynamic Water Cluster",
    "GeoMicroBio Cluster",
    "Urban Cluster",
    "CZNet Hub",
]

legacy_clusters = [
    "CZO Boulder",
    "CZO Calhoun",
    "CZO Sierra",
    "CZO Catalina-Jemez",
    "CZO Christina",
    "CZO Eel",
    "CZO IML",
    "CZO Luquillo",
    "CZO National",
    "CZO Reynolds",
    "CZO Shale-Hills",
]

all_clusters = current_clusters + legacy_clusters
