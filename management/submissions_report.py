import asyncio

import motor
from beanie import init_beanie

from dspback.config import get_settings
from dspback.pydantic_schemas import User, Submission
from dspback.utils.jsonld.clusters import cluster_by_id

'''
This script generates a report for the number of discoverable submissions, funding identifiers and clusters.

Example call:

docker exec dspback python management/submission_report.py
'''

async def initiaize_beanie():
    db = motor.motor_asyncio.AsyncIOMotorClient(get_settings().mongo_url)
    await init_beanie(
        database=db[get_settings().mongo_database], document_models=[User, Submission]
    )
    return db[get_settings().mongo_database]

async def main():
    db = await initiaize_beanie()

    submission_count_by_repository = {}
    test_submission_count_by_repository = {}
    submission_count_by_cluster = {}
    funding_by_cluster = {}
    submission_count_by_funding = {}
    private_document_count = 0
    discoverable_documents_count = 0
    for submission in await Submission.all().to_list():
        if "test" == submission.title.lower() or "asdf" in submission.title:
            submission_count = test_submission_count_by_repository.get(str(submission.repo_type), 0)
            test_submission_count_by_repository[str(submission.repo_type)] = submission_count + 1
        else:
            submission_count = submission_count_by_repository.get(str(submission.repo_type), 0)
            submission_count_by_repository[str(submission.repo_type)] = submission_count + 1

        discovery_document = await db["discovery"].find_one({"repository_identifier": submission.identifier})
        if discovery_document:
            discoverable_documents_count = discoverable_documents_count + 1
            for cluster in discovery_document.get("clusters", []):
                cluster_count = submission_count_by_cluster.get(cluster, 0)
                submission_count_by_cluster[cluster] = cluster_count + 1

            if "funding" in discovery_document:
                for funding in discovery_document["funding"]:
                    funding_identifier = funding.get("identifier", None)

                    funding_id_match = None
                    cluster_match = None
                    for cluster_funding_id, cluster in cluster_by_id.items():
                        if cluster_funding_id in funding_identifier:
                            funding_id_match= cluster_funding_id
                            cluster_match = cluster
                            break
                    if funding_id_match:
                        funding_ids = funding_by_cluster.get(cluster, set())
                        funding_ids.update([funding_id_match])
                        funding_by_cluster[cluster_match] = funding_ids
                        submission_count = submission_count_by_funding.get(cluster_match, 0)
                        submission_count_by_funding[cluster_match] = submission_count + 1
        else:
            private_document_count = private_document_count + 1
    print("Submission Count By Repository (Discoverable and private)")
    print(submission_count_by_repository)
    print("\nTest submission count by repository")
    print(test_submission_count_by_repository)
    print("\nSubmission count by cluster (Discoverable Submissions)")
    print(submission_count_by_cluster)
    print("\nSubmission Funding identifiers by cluster (Discoverable Submissions)")
    print(funding_by_cluster)
    print("\nSubmission count by funding identifier (Discoverable Submissions)")
    print(submission_count_by_funding)
    print("\nNumber of documents not discoverable")
    print(private_document_count)
    print("\nNumber of documents discoverable")
    print(discoverable_documents_count)


if __name__ == "__main__":
    asyncio.run(main())