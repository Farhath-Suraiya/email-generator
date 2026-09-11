import json
import random
from pathlib import Path

CATEGORIES = [
    "Meeting",
    "Scheduling",
    "Customer Support",
    "Internship/Job",
    "Leave Request",
    "Project Update",
    "Document Request",
    "Follow-up",
    "Payment/Billing",
    "Technical Issue",
    "Apology",
    "Confirmation",
    "Invitation",
    "Information Request",
    "Professional Networking"
]

# Templates for each category containing email components, tones, and realistic reply pairings

TEMPLATES = {
    "Meeting": [
        {
            "incoming": "Hi {name},\n\nCan we set up a quick 30-minute sync regarding the {topic}? Please let me know your availability for {day}.\n\nBest,\n{sender}",
            "reply": "Hi {sender},\n\nThanks for reaching out. I'm available on {day} between {time_window}. Let me know what time works best for you and send over an invite.\n\nBest regards,\n{name}",
            "topics": ["Q3 roadmap alignment", "upcoming product release", "client feedback review", "marketing budget approval", "sprint retrospective"],
            "days": ["this Tuesday", "this Thursday", "next Monday morning", "Friday afternoon"],
            "windows": ["10:00 AM - 12:00 PM", "2:00 PM - 4:00 PM", "11:00 AM - 1:00 PM"]
        },
        {
            "incoming": "Dear {name},\n\nWe need to discuss the urgent updates on the {topic}. Could we meet today or tomorrow?\n\nRegards,\n{sender}",
            "reply": "Dear {sender},\n\nI can make time today at {time_single} or tomorrow at {time_single2}. Please confirm which works for you.\n\nRegards,\n{name}",
            "topics": ["security audit findings", "server migration plan", "Q4 budget reallocation", "vendor contract renewal"],
            "days": [],
            "windows": []
        },
        {
            "incoming": "Hello {name},\n\nFollowing up on our project milestones, I would like to schedule a review meeting with the team. Are you free {day}?\n\nBest,\n{sender}",
            "reply": "Hello {sender},\n\n{day} works well for me. I can join after {time_single}. Looking forward to the update.\n\nBest,\n{name}",
            "topics": ["UX redesign milestone", "frontend integration progress", "data pipeline validation"],
            "days": ["this Wednesday", "next Tuesday", "tomorrow afternoon"],
            "windows": []
        },
        {
            "incoming": "Hi {name},\n\nCould you host a brief call to align on {topic}? Let me know when you have 15 minutes to spare.\n\nThanks,\n{sender}",
            "reply": "Hi {sender},\n\nI'm free at {time_single} today. Feel free to give me a call then or send a calendar invite.\n\nThanks,\n{name}",
            "topics": ["API integration details", "design sign-off", "performance evaluation feedback"],
            "days": [],
            "windows": []
        }
    ],
    "Scheduling": [
        {
            "incoming": "Hi {name},\n\nI noticed a conflict with our scheduled meeting on {day} at {time_single}. Can we reschedule to later in the week?\n\nThanks,\n{sender}",
            "reply": "Hi {sender},\n\nNo problem at all. How about we reschedule to {day2} at {time_single2}? Let me know if that suits your schedule.\n\nBest,\n{name}",
            "topics": [],
            "days": ["Monday", "Tuesday", "Wednesday"],
            "windows": []
        },
        {
            "incoming": "Dear {name},\n\nPlease let me know your available slots for the upcoming {topic} workshop next week.\n\nBest,\n{sender}",
            "reply": "Dear {sender},\n\nI am available on Tuesday from 9:00 AM to 12:00 PM and Thursday after 2:00 PM. Please feel free to schedule accordingly.\n\nBest regards,\n{name}",
            "topics": ["AI Governance", "Design Systems", "Cloud Migration Strategy", "Agile Operations"],
            "days": [],
            "windows": []
        },
        {
            "incoming": "Hi {name},\n\nCan we move our recurring one-on-one from {day} to {day2}? Something urgent came up.\n\nThanks,\n{sender}",
            "reply": "Hi {sender},\n\nSure, moving our 1:1 to {day2} works fine for me. I've updated my calendar.\n\nBest,\n{name}",
            "topics": [],
            "days": ["Monday", "Wednesday"],
            "windows": []
        },
        {
            "incoming": "Hello {name},\n\nCould you send over calendar invites for the candidate interview loop scheduled for {day}?\n\nRegards,\n{sender}",
            "reply": "Hello {sender},\n\nI have sent out the invites to all panel members for {day}. Let me know if you need any changes.\n\nRegards,\n{name}",
            "topics": [],
            "days": ["this Thursday", "next Friday"],
            "windows": []
        }
    ],
    "Customer Support": [
        {
            "incoming": "Hello Support Team,\n\nI am experiencing an issue with order #{order_id}. The items received do not match my receipt. Please assist.\n\nThanks,\n{sender}",
            "reply": "Hello {sender},\n\nThank you for bringing this to our attention. We apologize for the error with order #{order_id}. We have initiated a replacement shipment today, and you will receive tracking information shortly.\n\nBest regards,\n{name}\nCustomer Support",
            "topics": [],
            "days": [],
            "windows": []
        },
        {
            "incoming": "Hi,\n\nI submitted a refund request for invoice #{order_id} 5 days ago, but I haven't received any confirmation or update.\n\nRegards,\n{sender}",
            "reply": "Hi {sender},\n\nThank you for reaching out. I checked your account status for invoice #{order_id}. The refund was processed yesterday and should reflect in your account within 3-5 business days.\n\nBest,\n{name}\nSupport Specialist",
            "topics": [],
            "days": [],
            "windows": []
        },
        {
            "incoming": "Dear Team,\n\nMy account access was blocked after entering the wrong password. Could you please unlock account {email_addr}?\n\nThanks,\n{sender}",
            "reply": "Dear {sender},\n\nI have unlocked your account ({email_addr}) and triggered a password reset link to your registered email. Please follow the link to set a new password.\n\nRegards,\n{name}\nTechnical Support",
            "topics": [],
            "days": [],
            "windows": []
        },
        {
            "incoming": "Hello,\n\nIs it possible to upgrade my monthly subscription to an annual enterprise plan for account #{order_id}?\n\nBest,\n{sender}",
            "reply": "Hello {sender},\n\nYes, absolutely! I have upgraded your subscription for account #{order_id} to our Annual Enterprise Plan. A pro-rated invoice has been emailed to you.\n\nBest regards,\n{name}\nCustomer Success",
            "topics": [],
            "days": [],
            "windows": []
        }
    ],
    "Internship/Job": [
        {
            "incoming": "Dear {name},\n\nI am writing to express my interest in the {role} position at your company. Attached is my resume for your review.\n\nSincerely,\n{sender}",
            "reply": "Dear {sender},\n\nThank you for your application for the {role} role. We have received your resume and our recruiting team is currently reviewing applications. We will reach out if your background matches our requirements.\n\nBest regards,\n{name}\nTalent Acquisition",
            "roles": ["Software Engineer Intern", "Product Manager", "Data Analyst Intern", "Frontend Engineer", "DevOps Specialist"]
        },
        {
            "incoming": "Hi {name},\n\nThank you for taking the time to interview me yesterday for the {role} position. I enjoyed learning more about the team.\n\nBest regards,\n{sender}",
            "reply": "Hi {sender},\n\nThank you for your email! It was a pleasure speaking with you as well. We are completing interviews this week and expect to provide feedback by early next week.\n\nBest,\n{name}\nRecruiting Lead",
            "roles": ["Senior Backend Developer", "UX Designer", "AI Research Intern", "Solutions Architect"]
        },
        {
            "incoming": "Dear {name},\n\nI am following up on my interview for the {role} role held on {day}. Could you provide any status update?\n\nThanks,\n{sender}",
            "reply": "Dear {sender},\n\nThank you for following up. The hiring manager is currently finalizing evaluations. I hope to share formal feedback with you by {day2}.\n\nRegards,\n{name}\nHR Partner",
            "roles": ["Machine Learning Engineer", "Full Stack Engineer"],
            "days": ["last Tuesday", "last Friday"]
        },
        {
            "incoming": "Dear Recruiting Team,\n\nI would like to confirm my acceptance of the internship offer for the upcoming summer cohort.\n\nSincerely,\n{sender}",
            "reply": "Dear {sender},\n\nWonderful news! We are thrilled to welcome you to our summer cohort. Our onboarding team will send your welcome packet and contract details shortly.\n\nWarm regards,\n{name}\nUniversity Recruiting",
            "roles": []
        }
    ],
    "Leave Request": [
        {
            "incoming": "Hi {name},\n\nI would like to request annual leave from {day} to {day2} for personal reasons. I will ensure my pending tasks are handed over to {colleague}.\n\nBest,\n{sender}",
            "reply": "Hi {sender},\n\nYour leave request from {day} to {day2} has been approved. Please make sure {colleague} has access to all necessary files before you head out.\n\nBest,\n{name}",
            "topics": [],
            "days": ["October 12th", "November 3rd", "December 20th"],
            "days2": ["October 16th", "November 7th", "December 30th"]
        },
        {
            "incoming": "Dear {name},\n\nI am feeling unwell today and will not be able to attend work. I will be taking sick leave today.\n\nRegards,\n{sender}",
            "reply": "Dear {sender},\n\nThanks for letting me know. Take care and get well soon! Please log your sick leave in the portal when you're back.\n\nRegards,\n{name}",
            "topics": [],
            "days": [],
            "days2": []
        },
        {
            "incoming": "Hi {name},\n\nI am requesting 2 days of emergency leave starting tomorrow due to a family matter.\n\nThanks,\n{sender}",
            "reply": "Hi {sender},\n\nApproved. Please take care of your family matter. Let me know if you need any additional time off.\n\nBest regards,\n{name}",
            "topics": [],
            "days": [],
            "days2": []
        },
        {
            "incoming": "Dear {name},\n\nI am submitting a request for parental leave starting next month. I have detailed the coverage plan in the attached document.\n\nSincerely,\n{sender}",
            "reply": "Dear {sender},\n\nThank you for submitting your coverage plan. Your parental leave request is approved. HR will coordinate with you regarding formal paperwork.\n\nWarm regards,\n{name}",
            "topics": [],
            "days": [],
            "days2": []
        }
    ],
    "Project Update": [
        {
            "incoming": "Hi {name},\n\nHere is a quick update on {topic}: phase 1 is complete and we are starting phase 2 ahead of schedule.\n\nBest,\n{sender}",
            "reply": "Hi {sender},\n\nGreat progress! Thanks to the team for the hard work. Please keep me posted on the phase 2 benchmarks.\n\nBest,\n{name}",
            "topics": ["the database migration", "the payment gateway integration", "the mobile app refactoring", "the microservice extraction"]
        },
        {
            "incoming": "Dear {name},\n\nUnfortunately, we encountered a blocker on {topic} due to third-party API latency. We may experience a 2-day delay.\n\nRegards,\n{sender}",
            "reply": "Dear {sender},\n\nThank you for flagging this early. Let's discuss mitigation options during tomorrow's standup. Keep us updated on vendor responses.\n\nRegards,\n{name}",
            "topics": ["the authentication module", "the third-party analytics sync", "the search index pipeline"]
        },
        {
            "incoming": "Hello {name},\n\nThe weekly status report for {topic} is now available on the internal portal. Key metric: conversion increased by {percent}%.\n\nBest,\n{sender}",
            "reply": "Hello {sender},\n\nExcellent results on the {percent}% conversion bump! Thank you for sharing the report.\n\nBest regards,\n{name}",
            "topics": ["the Q3 marketing campaign", "the onboarding flow experiment", "the recommendation engine test"]
        },
        {
            "incoming": "Hi {name},\n\nAll QA tests for {topic} passed successfully. We are ready to deploy to production tomorrow at 10 AM.\n\nThanks,\n{sender}",
            "reply": "Hi {sender},\n\nAwesome news! Green light for production deployment tomorrow at 10 AM. I will be on standby.\n\nThanks,\n{name}",
            "topics": ["release v2.4.0", "the billing fix patch", "the security hotfix"]
        }
    ],
    "Document Request": [
        {
            "incoming": "Hi {name},\n\nCould you please share the latest version of the {doc_type}? We need it for the client review.\n\nThanks,\n{sender}",
            "reply": "Hi {sender},\n\nI have attached the updated {doc_type} to this email. Let me know if you need any additional sections added.\n\nBest,\n{name}",
            "doc_types": ["Q3 Financial Summary", "Technical Architecture Diagram", "Security Compliance Report", "Client Onboarding Deck"]
        },
        {
            "incoming": "Dear {name},\n\nCan you send over the signed copy of the {doc_type} for our records?\n\nRegards,\n{sender}",
            "reply": "Dear {sender},\n\nPlease find the fully executed {doc_type} attached. Let me know if everything looks complete.\n\nRegards,\n{name}",
            "doc_types": ["Non-Disclosure Agreement (NDA)", "Master Services Agreement (MSA)", "Statement of Work (SOW)"]
        },
        {
            "incoming": "Hello {name},\n\nWhere can I access the documentation for {doc_type}? I am unable to locate the link in our wiki.\n\nThanks,\n{sender}",
            "reply": "Hello {sender},\n\nYou can access the documentation for {doc_type} at our team wiki link: https://internal.wiki/docs/{doc_type_slug}. Let me know if you need permission access.\n\nBest,\n{name}",
            "doc_types": ["REST API Specifications", "Deployment Guidelines", "Disaster Recovery Plan"]
        },
        {
            "incoming": "Hi {name},\n\nCould you provide the export of the {doc_type} in PDF format by end of day?\n\nBest,\n{sender}",
            "reply": "Hi {sender},\n\nHere is the PDF export of the {doc_type} as requested. Let me know if you have any questions.\n\nBest,\n{name}",
            "doc_types": ["Quarterly Audit Results", "Product Release Notes v3.1"]
        }
    ],
    "Follow-up": [
        {
            "incoming": "Hi {name},\n\nFollowing up on my previous email regarding {topic}. Have you had a chance to look into this?\n\nBest,\n{sender}",
            "reply": "Hi {sender},\n\nThanks for following up. I am currently reviewing {topic} and will provide a full response by EOD today.\n\nBest regards,\n{name}",
            "topics": ["the contract revision", "the feature request proposal", "the infrastructure budget", "the design mockups"]
        },
        {
            "incoming": "Dear {name},\n\nJust checking in to see if you've received the quote for {topic} sent last week.\n\nRegards,\n{sender}",
            "reply": "Dear {sender},\n\nYes, I received the quote. We are evaluating it internally and will get back to you with our decision by Friday.\n\nRegards,\n{name}",
            "topics": ["cloud hosting services", "pen-testing audit", "hardware procurement"]
        },
        {
            "incoming": "Hi {name},\n\nI wanted to follow up on the status of our ticket #{order_id}. Any updates from engineering?\n\nThanks,\n{sender}",
            "reply": "Hi {sender},\n\nEngineering is actively investigating ticket #{order_id}. We expect a patch release later today and will notify you immediately.\n\nThanks,\n{name}",
            "topics": []
        },
        {
            "incoming": "Hello {name},\n\nFollowing up on the decision for {topic}. The team is waiting for approval to proceed.\n\nBest,\n{sender}",
            "reply": "Hello {sender},\n\nApologies for the delay! The proposal for {topic} is approved. You have green light to move forward.\n\nBest,\n{name}",
            "topics": ["the Q4 hiring plan", "the vendor selection", "the domain migration"]
        }
    ],
    "Payment/Billing": [
        {
            "incoming": "Dear Finance Team,\n\nPlease find attached invoice #{order_id} for services rendered in {month}. Kindly confirm receipt.\n\nRegards,\n{sender}",
            "reply": "Dear {sender},\n\nReceipt confirmed for invoice #{order_id}. It has been forwarded to accounts payable for processing on the scheduled payout date.\n\nBest regards,\n{name}\nFinance Dept",
            "months": ["September", "October", "November", "December"]
        },
        {
            "incoming": "Hi {name},\n\nWe noticed an unexpected charge of ${amount} on our monthly invoice #{order_id}. Could you clarify what this is for?\n\nThanks,\n{sender}",
            "reply": "Hi {sender},\n\nThank you for flagging this. The ${amount} charge on invoice #{order_id} was due to additional compute seat usage last month. I have attached the detailed usage breakdown.\n\nBest,\n{name}",
            "amounts": ["150", "320", "500", "1,200"]
        },
        {
            "incoming": "Dear {name},\n\nOur account reflects an overdue balance for invoice #{order_id}. Please submit payment to prevent service interruption.\n\nSincerely,\n{sender}",
            "reply": "Dear {sender},\n\nThank you for the notice. Payment for invoice #{order_id} was submitted today via wire transfer. Please confirm once settled.\n\nRegards,\n{name}",
            "months": []
        },
        {
            "incoming": "Hello {name},\n\nCould you update our billing contact email to {email_addr} starting next billing cycle?\n\nBest,\n{sender}",
            "reply": "Hello {sender},\n\nI have updated your billing email address to {email_addr} in our system. All future invoices will be sent there.\n\nBest regards,\n{name}",
            "months": []
        }
    ],
    "Technical Issue": [
        {
            "incoming": "Hi Tech Support,\n\nOur users are reporting a 500 error when submitting the checkout form on {service}. Please investigate urgently.\n\nThanks,\n{sender}",
            "reply": "Hi {sender},\n\nWe identified the issue causing 500 errors on {service}—it was a database connection pool exhaustion. A hotfix has been deployed and checkout is restored.\n\nBest regards,\n{name}\nDevOps Team",
            "services": ["the web app", "the customer portal", "the iOS app", "the payment gateway"]
        },
        {
            "incoming": "Dear Team,\n\nThe SSH access to server {server_name} is failing with connection timeout.\n\nRegards,\n{sender}",
            "reply": "Dear {sender},\n\nThe firewall rule for server {server_name} was updated. SSH connectivity has been restored. Please try logging in now.\n\nRegards,\n{name}\nSysAdmin",
            "servers": ["prod-db-01", "staging-api-02", "auth-service-node-03"]
        },
        {
            "incoming": "Hello {name},\n\nThe nightly data synchronization pipeline failed at 03:00 AM with exit code 1.\n\nBest,\n{sender}",
            "reply": "Hello {sender},\n\nThanks for flagging. The pipeline failure was caused by a malformed schema in incoming raw logs. I re-ran the job after filtering bad records and sync is complete.\n\nBest,\n{name}\nData Operations",
            "servers": []
        },
        {
            "incoming": "Hi Support,\n\nIs there an ongoing outage on {service}? Response times are taking over 10 seconds.\n\nThanks,\n{sender}",
            "reply": "Hi {sender},\n\nYes, we experienced elevated latency on {service} due to a traffic spike. Auto-scaling has added capacity and latency is back below 200ms.\n\nThanks,\n{name}\nSite Reliability Engineer",
            "services": ["the Search API", "the Image CDN", "the Analytics Dashboard"]
        }
    ],
    "Apology": [
        {
            "incoming": "Dear {name},\n\nI sincerely apologize for missing our meeting scheduled for {day} at {time_single}. An urgent client emergency required my immediate attention.\n\nSincerely,\n{sender}",
            "reply": "Dear {sender},\n\nNo worries at all, I completely understand that urgent matters come up. Let me know when you'd like to reschedule.\n\nBest regards,\n{name}",
            "days": ["this morning", "yesterday afternoon"]
        },
        {
            "incoming": "Hi {name},\n\nApologies for the oversight in the latest report draft for {topic}. I attached the corrected document here.\n\nThanks,\n{sender}",
            "reply": "Hi {sender},\n\nThank you for sending over the corrected draft for {topic}. No problem at all, I appreciate the prompt update.\n\nBest,\n{name}",
            "topics": ["Q2 Financials", "Marketing Metrics", "User Growth Report"]
        },
        {
            "incoming": "Hello {name},\n\nI apologize for the delay in responding to your email regarding {topic}.\n\nBest regards,\n{sender}",
            "reply": "Hello {sender},\n\nThanks for getting back to me! No problem about the delay. Let's proceed with {topic}.\n\nBest regards,\n{name}",
            "topics": ["the partnership offer", "the conference sponsorship"]
        },
        {
            "incoming": "Dear {name},\n\nPlease accept our sincere apologies for the service outage on {day}. We have taken measures to prevent recurrence.\n\nRegards,\n{sender}",
            "reply": "Dear {sender},\n\nThank you for the transparent communication and root-cause summary. We appreciate your team's quick resolution.\n\nRegards,\n{name}",
            "days": ["last Tuesday", "Sunday evening"]
        }
    ],
    "Confirmation": [
        {
            "incoming": "Hi {name},\n\nCan you confirm if you received the updated requirements document for {topic}?\n\nThanks,\n{sender}",
            "reply": "Hi {sender},\n\nYes, I confirm that I have received the updated requirements document for {topic}. We will review it shortly.\n\nThanks,\n{name}",
            "topics": ["the mobile app redesign", "the cloud migration project"]
        },
        {
            "incoming": "Dear {name},\n\nPlease confirm your attendance at the annual strategy summit on {day}.\n\nBest,\n{sender}",
            "reply": "Dear {sender},\n\nI am pleased to confirm my attendance at the annual strategy summit on {day}. Looking forward to it.\n\nBest regards,\n{name}",
            "days": ["November 15th", "December 5th"]
        },
        {
            "incoming": "Hello {name},\n\nJust confirming that order #{order_id} has been processed for delivery.\n\nRegards,\n{sender}",
            "reply": "Hello {sender},\n\nThank you for the confirmation regarding order #{order_id}. We look forward to receiving the shipment.\n\nRegards,\n{name}",
            "days": []
        },
        {
            "incoming": "Hi {name},\n\nPlease confirm if the wire transfer of ${amount} for invoice #{order_id} was received by your bank.\n\nThanks,\n{sender}",
            "reply": "Hi {sender},\n\nYes, we confirm receipt of the ${amount} wire transfer for invoice #{order_id}. Thank you for the quick payment settlement.\n\nBest,\n{name}",
            "amounts": ["2,500", "10,000", "4,750"]
        }
    ],
    "Invitation": [
        {
            "incoming": "Hi {name},\n\nYou are cordially invited to speak at our annual {topic} conference on {day}. We would be honored to have your insights.\n\nBest regards,\n{sender}",
            "reply": "Hi {sender},\n\nThank you so much for the invitation! I would be delighted to speak at the {topic} conference on {day}. Please send over the speaker guidelines.\n\nWarm regards,\n{name}",
            "topics": ["Tech Leadership", "AI in Industry", "Cybersecurity Frontiers"],
            "days": ["October 24th", "November 12th"]
        },
        {
            "incoming": "Dear {name},\n\nPlease join us for our team celebratory dinner this {day} at 7 PM at {location}.\n\nBest,\n{sender}",
            "reply": "Dear {sender},\n\nThanks for inviting me! I will definitely be there to celebrate with the team at {location} on {day}.\n\nBest regards,\n{name}",
            "days": ["Friday", "Thursday evening"],
            "locations": ["Bistro Central", "The Grand Grill", "Harbor View Restaurant"]
        },
        {
            "incoming": "Hello {name},\n\nWe invite you to participate in our beta user testing session for {topic} next week.\n\nRegards,\n{sender}",
            "reply": "Hello {sender},\n\nThank you for the invitation. I would love to test out the beta for {topic} and provide feedback. Please send over the schedule options.\n\nRegards,\n{name}",
            "topics": ["the new analytics workspace", "the desktop app v3", "the collaborative editor"]
        },
        {
            "incoming": "Hi {name},\n\nYou are invited to join the advisory panel for {topic}. Would you be open to a 20-minute onboarding call?\n\nBest,\n{sender}",
            "reply": "Hi {sender},\n\nI am honored by the invitation to join the advisory panel. I am happy to hop on an onboarding call next week.\n\nBest,\n{name}",
            "topics": ["Open Source AI Initiative", "Startup Incubator Program"]
        }
    ],
    "Information Request": [
        {
            "incoming": "Hi {name},\n\nCould you provide details regarding the pricing tiers for {service}?\n\nThanks,\n{sender}",
            "reply": "Hi {sender},\n\nSure! Our {service} offers three tiers: Starter ($29/mo), Professional ($99/mo), and Enterprise (Custom pricing). I have attached the full feature breakdown matrix.\n\nBest regards,\n{name}",
            "services": ["our API subscription", "our Managed Cloud Hosting", "our Security Monitoring Tool"]
        },
        {
            "incoming": "Dear {name},\n\nWhat are the system requirements for installing the software version {version}?\n\nRegards,\n{sender}",
            "reply": "Dear {sender},\n\nVersion {version} requires 64-bit OS (Linux/Windows/macOS), at least 8GB RAM, 4 CPU cores, and Python 3.10+. Full specs are available on our documentation page.\n\nRegards,\n{name}",
            "versions": ["v4.2.0", "v5.0-beta", "v3.8.1"]
        },
        {
            "incoming": "Hello {name},\n\nCan you explain the retention policy for user data on our platform?\n\nBest,\n{sender}",
            "reply": "Hello {sender},\n\nOur data retention policy keeps active user data for the duration of the account plus 30 days post-cancellation, after which it is permanently purged per GDPR compliance.\n\nBest,\n{name}",
            "services": []
        },
        {
            "incoming": "Hi {name},\n\nCould you clarify the SLA guaranteed uptime for our enterprise instance?\n\nThanks,\n{sender}",
            "reply": "Hi {sender},\n\nOur enterprise tier guarantees a 99.9% uptime SLA with 24/7 dedicated support and a 15-minute response time for critical issues.\n\nThanks,\n{name}",
            "services": []
        }
    ],
    "Professional Networking": [
        {
            "incoming": "Hi {name},\n\nI came across your work on {topic} and was impressed by your recent talk. I'd love to connect and exchange ideas.\n\nBest,\n{sender}",
            "reply": "Hi {sender},\n\nThank you for reaching out! I'm always glad to connect with fellow professionals passionate about {topic}. Let's stay in touch.\n\nBest regards,\n{name}",
            "topics": ["scalable vector retrieval", "LLM fine-tuning", "distributed database architectures", "zero-trust security"]
        },
        {
            "incoming": "Dear {name},\n\nWe met briefly at the {event} conference. I am interested in exploring potential partnership opportunities between our teams.\n\nRegards,\n{sender}",
            "reply": "Dear {sender},\n\nIt was great meeting you at {event}! I'd be happy to explore potential collaboration opportunities. Let's schedule a brief intro call next week.\n\nRegards,\n{name}",
            "events": ["TechCrunch Disrupt", "AI World Summit", "PyCon Global", "Cloud Native Expo"]
        },
        {
            "incoming": "Hello {name},\n\nI am an alumnus of {university} working in tech leadership. I saw your profile and would love to offer career advice or network.\n\nBest,\n{sender}",
            "reply": "Hello {sender},\n\nGreat to connect with a fellow {university} alum! I'd appreciate the opportunity to chat and hear about your experience in tech leadership.\n\nBest,\n{name}",
            "universities": ["Stanford University", "MIT", "UC Berkeley", "Carnegie Mellon", "University of Michigan"]
        },
        {
            "incoming": "Hi {name},\n\nI follow your articles on tech trends. Would you be open to an informal virtual coffee chat sometime this month?\n\nThanks,\n{sender}",
            "reply": "Hi {sender},\n\nThanks for reading my articles! I'd be happy to hop on a virtual coffee chat. Feel free to pick a time on my calendar link.\n\nBest,\n{name}",
            "topics": []
        }
    ]
}

NAMES = ["Alice Smith", "Bob Jones", "Charlie Brown", "Diana Prince", "Evan Wright", "Fiona Gallagher", "George Clark", "Hannah Abbott", "Ian Malcolm", "Julia Roberts"]
SENDERS = ["David Miller", "Sarah Jenkins", "Michael Scott", "Emily Watson", "Alex Rivera", "Jessica Taylor", "Daniel Kim", "Rachel Green", "Chris Hemsworth", "Laura Palmer"]
COLLEAGUES = ["Mark Davis", "Samantha Reed", "Kevin Zhang", "Olivia Vance", "Tom Holland"]
EMAILS = ["alex.r@example.com", "jessica.t@partnercorp.org", "daniel.k@techcorp.io", "rachel.g@company.com"]

def generate_records(target_count=650):
    records = []
    record_id = 1
    seen_hashes = set()
    
    cat_target = (target_count // len(CATEGORIES)) + 5
    
    for category in CATEGORIES:
        cat_templates = TEMPLATES[category]
        count_for_cat = 0
        
        while count_for_cat < cat_target:
            template_info = random.choice(cat_templates)
            name = random.choice(NAMES)
            sender = random.choice(SENDERS)
            colleague = random.choice(COLLEAGUES)
            email_addr = random.choice(EMAILS)
            order_id = str(random.randint(10000, 99999))
            time_single = f"{random.randint(1, 12)}:00 {random.choice(['AM', 'PM'])}"
            time_single2 = f"{random.randint(1, 12)}:30 {random.choice(['AM', 'PM'])}"
            percent = str(random.randint(5, 45))
            
            topic = random.choice(template_info.get("topics", ["the core service"])) if template_info.get("topics") else "the core service"
            day = random.choice(template_info.get("days", ["this Thursday"])) if template_info.get("days") else "this Thursday"
            day2 = random.choice(template_info.get("days2", ["next Friday"])) if template_info.get("days2") else "next Friday"
            time_window = random.choice(template_info.get("windows", ["2:00 PM - 4:00 PM"])) if template_info.get("windows") else "2:00 PM - 4:00 PM"
            role = random.choice(template_info.get("roles", ["Software Engineer"])) if template_info.get("roles") else "Software Engineer"
            doc_type = random.choice(template_info.get("doc_types", ["Project Plan"])) if template_info.get("doc_types") else "Project Plan"
            doc_type_slug = doc_type.lower().replace(" ", "-").replace("(", "").replace(")", "")
            amount = random.choice(template_info.get("amounts", ["500"])) if template_info.get("amounts") else "500"
            month = random.choice(template_info.get("months", ["October"])) if template_info.get("months") else "October"
            service = random.choice(template_info.get("services", ["the cloud service"])) if template_info.get("services") else "the cloud service"
            server_name = random.choice(template_info.get("servers", ["prod-api-01"])) if template_info.get("servers") else "prod-api-01"
            location = random.choice(template_info.get("locations", ["Downtown Bistro"])) if template_info.get("locations") else "Downtown Bistro"
            version = random.choice(template_info.get("versions", ["v2.0"])) if template_info.get("versions") else "v2.0"
            event = random.choice(template_info.get("events", ["Global Tech Conference"])) if template_info.get("events") else "Global Tech Conference"
            university = random.choice(template_info.get("universities", ["State University"])) if template_info.get("universities") else "State University"

            kwargs = {
                "name": name,
                "sender": sender,
                "colleague": colleague,
                "email_addr": email_addr,
                "order_id": order_id,
                "time_single": time_single,
                "time_single2": time_single2,
                "percent": percent,
                "topic": topic,
                "day": day,
                "day2": day2,
                "time_window": time_window,
                "role": role,
                "doc_type": doc_type,
                "doc_type_slug": doc_type_slug,
                "amount": amount,
                "month": month,
                "service": service,
                "server_name": server_name,
                "location": location,
                "version": version,
                "event": event,
                "university": university
            }

            try:
                incoming = template_info["incoming"].format(**kwargs)
                reply = template_info["reply"].format(**kwargs)
            except KeyError:
                continue

            pair_hash = hash((incoming, reply))
            if pair_hash in seen_hashes:
                continue
            
            seen_hashes.add(pair_hash)
            records.append({
                "id": f"EML-{record_id:04d}",
                "category": category,
                "incoming_email": incoming,
                "reference_reply": reply
            })
            record_id += 1
            count_for_cat += 1

    return records

def main():
    random.seed(42)
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "emails.json"

    records = generate_records(target_count=650)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated {len(records)} email/reply pairs saved to {output_file}")

if __name__ == "__main__":
    main()
