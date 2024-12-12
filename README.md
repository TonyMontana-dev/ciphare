# Ciphare - A web application 
With loads of files exchanged every day, data privacy and secure file sharing have become crucial in today’s world. As technology evolves, there’s an increasing need for people and organizations to share sensitive information without risking data breaches or unauthorized access. This Capstone project aims to meet this need by providing a secure, web-based platform that allows users to encrypt and decrypt various file types including documents, photos, and audio files using the military-grade AES-256 encryption algorithm. Launching this project will offer a reliable, user-friendly solution for sharing files temporarily, with added security features like expiration times, limits on decryption, shareable features (such as a link to share), and multiple selections of algorithms. I was inspired by services like EnvShare, Hat.sh, Cyberchef, and OnionShare which emphasize private, temporary file storage, focus on security and encryption, and various tools/methods related to cryptography and cybersecurity. However, this project will be an exhaustive tentative attempt to differentiate by integrating new functionalities, such as the encryption/decryption of any file type, implementing a web interface, and a community space where users can exchange ideas, questions, and more. Furthermore, this project intends to be more versatile by offering users a choice of multiple encryption algorithms, making it adaptable to a wider variety of security needs. This project aims to support the larger cybersecurity and privacy community by providing a dependable secure, temporary file sharing tool. It serves anyone needing a secure method for transferring files, including journalists, legal professionals, and NGOs operating in high-risk Andrea Marcelli 1Andrea Marcelli CPSC 49200 003 December 11th, 2024 Project Manual settings where secure information transmission is essential. By offering temporary file storage and self-destructing download links, this platform minimizes the long-term exposure of sensitive data, giving users better control over their information. Ultimately, this project empowers individuals and organizations to communicate securely, with peace of mind that their data is protected by advanced encryption standards. Through this research and development, I hope to contribute a valuable tool to the cybersecurity community and lay a solid foundation for future work in secure digital communication. It also encompasses possible further implementation to expand this project including community-focused features related to privacy and security, a mobile application, the addition of various cybersecurity tools, and more.

# Installation step-by-step
The following is a restricted list of dependencies that are crucial to this project: 
- Flask: Backend framework for API development.
- Next.js: Frontend framework for building user interfaces.
- TypeScript: Ensures type safety in the frontend code.
- Redis: Used for storing encrypted files and managing TTL and READS.
- Upstash Redis: Cloud-based Redis solution for scalability.
- Cryptography: Python library for implementing encryption algorithms.
- Tailwind CSS: Utility-first CSS framework for styling the front end.

The following are the instructions on how to run this project or your local environment: 

Clone the repository: 
git clone https://github.com/TonyMontana-dev/ciphare.git 

Move into the directory:
cd ciphare 

Install backend dependencies: pip install -r requirements.txt 

Install frontend dependencies: npm install 

Set up environment variables: 
- UPSTASH_REDIS_URL 
- UPSTASH_REDIS_PASSWORD 
- NEXT_PUBLIC_API_BASE_URL 
- DOMAIN 
- PORT 

Start the backend: flask run or python (or python3 based on your python version) FLASK INDEX/APP.PY MAIN FILE PATH 
Start the frontend: npm run dev 

# Features
- The features included in this project are but not limited to the following: 
- Store temporarily encrypted files 
- Store with a TTL(time to live) the encrypted files. 
- Store with a TAR (total amount of Reads). Therefore the file can be read/decrypted only X times 
- Use AES-256 encryption algorithm and multiple other algorithms 
- Input files of any type (PDF, JPEG, PNG, MP4, etc…) 
- Download the files aside from only sharing 
- Provide a sharable link for the encrypted data 
- Anonymous Community Posting 
- Modern User Interface
