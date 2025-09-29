from src.job_parser import fetch_job_description

data = fetch_job_description("https://www.glassdoor.it/Lavoro/londra-inghilterra-regno-unito-ai-engineer-lavori-SRCH_IL.0,30_IC2671300_KO31,42.htm")
print(data["title"])
print(data["description"])