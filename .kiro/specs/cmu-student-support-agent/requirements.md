# Requirements Document

## Introduction

The CMU Africa Student Support Agent is an AI-assisted email triage and response system that automates routine student inquiries while escalating complex, sensitive, or urgent cases to human staff. The system monitors a CMU Africa Gmail support mailbox, classifies incoming student requests, retrieves answers from approved institutional knowledge sources, generates responses, and manages the conversation workflow with appropriate human oversight.

## Glossary

- **Support_Agent**: The AI-assisted system that processes student emails
- **Email_Processor**: Component that receives and normalizes incoming Gmail messages
- **Triage_Service**: Component that classifies requests and determines urgency, sensitivity, and escalation requirements
- **RAG_Service**: Retrieval-Augmented Generation service that retrieves relevant content from the Knowledge_Base
- **Knowledge_Base**: Repository of approved CMU Africa institutional documents, handbooks, policies, and resources
- **Response_Generator**: Component that creates draft email responses based on retrieved knowledge
- **Response_Validator**: Component that verifies response quality, groundedness, and safety before sending
- **Escalation_Queue**: Queue of student requests that require human intervention
- **Approval_Queue**: Queue of AI-generated responses awaiting human approval before sending
- **Student_Email**: Incoming email message from a student to the support mailbox
- **Support_Staff**: Human staff members who review, approve, and handle escalated cases
- **Conversation_Thread**: Gmail thread representing one or more related email exchanges with a student
- **Grounded_Response**: AI-generated answer supported by specific evidence from approved Knowledge_Base sources
- **Confidence_Score**: Numerical measure (0.0 to 1.0) indicating the system's confidence in its classification or response
- **Resolution_Mode**: Classification determining how a request should be handled (AUTO_REPLY, HUMAN_REVIEW, or ESCALATE)
- **Admin_Dashboard**: Web interface providing operational visibility and analytics to Support_Staff

## Requirements

### Requirement 1: Email Monitoring and Ingestion

**User Story:** As a support staff member, I want the system to monitor the support mailbox continuously, so that student emails are processed without manual intervention.

#### Acceptance Criteria

1. THE Email_Processor SHALL connect to the designated CMU Africa Gmail support mailbox using secure authentication
2. WHEN a new Student_Email arrives in the monitored mailbox, THE Email_Processor SHALL retrieve it within 60 seconds
3. THE Email_Processor SHALL extract the message ID, thread ID, sender address, recipient address, subject, body text, timestamp, and attachment metadata
4. THE Email_Processor SHALL preserve the Gmail thread ID to maintain conversation context
5. THE Email_Processor SHALL store the original message content without modification
6. WHEN the Email_Processor successfully retrieves a Student_Email, THE Email_Processor SHALL forward the structured message data to the Triage_Service

### Requirement 2: Request Classification and Intent Detection

**User Story:** As the system, I want to understand what the student is asking, so that I can route the request appropriately.

#### Acceptance Criteria

1. WHEN the Triage_Service receives a Student_Email, THE Triage_Service SHALL identify the primary intent including "OTHER" as a valid classification result
2. THE Triage_Service SHALL classify requests into one or more of these categories: admissions, enrollment, registration, tuition, scholarships, financial questions, visa, accommodation, student induction, academic support, student success, courses, academic calendar, IT account access, campus facilities, events, student organizations, documents, deadlines, general information, technical support, or other
3. WHEN a Student_Email contains multiple distinct questions, THE Triage_Service SHALL identify all sub-intents
4. THE Triage_Service SHALL produce a Confidence_Score for each classification
5. WHEN classification Confidence_Score is below 0.70, THE Triage_Service SHALL mark the request for human review

### Requirement 3: Urgency Assessment

**User Story:** As a support staff member, I want the system to identify urgent requests, so that time-sensitive student needs are addressed promptly.

#### Acceptance Criteria

1. THE Triage_Service SHALL assign each Student_Email an urgency level: LOW, MEDIUM, HIGH, or CRITICAL using a precedence hierarchy where CRITICAL overrides HIGH, HIGH overrides MEDIUM, and MEDIUM overrides LOW
2. WHEN multiple urgency conditions apply, THE Triage_Service SHALL assign the most urgent classification according to the precedence hierarchy
3. WHEN a deadline falls within both 48-hour and 7-day windows, THE Triage_Service SHALL classify the request as CRITICAL (CRITICAL takes precedence over HIGH)
4. THE Triage_Service SHALL classify requests as CRITICAL when they reference imminent deadlines within 48 hours
5. THE Triage_Service SHALL classify requests as CRITICAL when they indicate student welfare concerns or emergencies
6. WHEN multiple welfare concerns are detected, THE Triage_Service SHALL assign urgency based on the most severe welfare condition
7. THE Triage_Service SHALL classify requests as HIGH when they reference deadlines within 7 days
8. THE Triage_Service SHALL classify requests as HIGH when they explicitly state urgency or time-sensitivity
9. THE Triage_Service SHALL classify routine informational questions as LOW urgency
10. WHEN urgency is CRITICAL, THE Triage_Service SHALL set Resolution_Mode to ESCALATE regardless of other factors

### Requirement 4: Sensitivity Detection and Escalation Rules

**User Story:** As a support staff member, I want the system to escalate sensitive cases to humans, so that students receive appropriate institutional judgment for complex situations.

#### Acceptance Criteria

1. THE Triage_Service SHALL assign each Student_Email a sensitivity level: LOW, MEDIUM, or HIGH
2. THE Triage_Service SHALL classify requests as HIGH sensitivity when they involve individual admission decisions or exceptions (mandatory, cannot be overridden)
3. THE Triage_Service SHALL classify requests as HIGH sensitivity when they involve requests to modify official student records (mandatory, cannot be overridden)
4. THE Triage_Service SHALL classify requests as HIGH sensitivity when they involve financial disputes or refund requests (mandatory, cannot be overridden)
5. THE Triage_Service SHALL classify requests as HIGH sensitivity when they involve legal matters, immigration complications, or complaints requiring institutional judgment (mandatory, cannot be overridden)
6. THE Triage_Service SHALL classify requests as HIGH sensitivity when they involve confidential student information or personal circumstances (mandatory, cannot be overridden)
7. THE Triage_Service SHALL classify requests as HIGH sensitivity when they contain threats or serious welfare concerns (mandatory, cannot be overridden)
8. WHEN sensitivity is HIGH, THE Triage_Service SHALL set Resolution_Mode to ESCALATE
9. WHEN a Student_Email is directed explicitly to a named staff member, THE Triage_Service SHALL set Resolution_Mode to ESCALATE
10. WHEN a LOW sensitivity case meets other escalation criteria, THE Triage_Service SHALL escalate the request

### Requirement 5: Resolution Mode Determination

**User Story:** As the system, I want to determine whether a request can be answered automatically or requires human involvement, so that safe automation and appropriate escalation are balanced.

#### Acceptance Criteria

1. THE Triage_Service SHALL assign each Student_Email one of three Resolution_Mode values: AUTO_REPLY, HUMAN_REVIEW, or ESCALATE
2. THE Triage_Service SHALL set Resolution_Mode to AUTO_REPLY when urgency is LOW, sensitivity is LOW, Confidence_Score is 0.85 or higher, and the request type is enabled for automation
3. THE Triage_Service SHALL set Resolution_Mode to HUMAN_REVIEW when urgency is LOW or MEDIUM, sensitivity is LOW or MEDIUM, and Confidence_Score is between 0.70 and 0.85
4. THE Triage_Service SHALL set Resolution_Mode to ESCALATE when urgency is CRITICAL, sensitivity is HIGH, Confidence_Score is below 0.70, or escalation rules are triggered
5. THE Triage_Service SHALL provide an escalation reason explanation for each request marked as ESCALATE

### Requirement 6: Knowledge Base Document Management

**User Story:** As a support staff member, I want the system to use only approved CMU Africa institutional resources, so that students receive accurate and authoritative information.

#### Acceptance Criteria

1. THE Knowledge_Base SHALL store CMU Africa institutional documents with metadata including document ID, title, source type, version, effective date, audience, and status
2. THE Knowledge_Base SHALL support these source types: official handbook, admission guide, policy document, website page, FAQ, internal support document, and announcement
3. THE Knowledge_Base SHALL maintain document version history
4. THE Knowledge_Base SHALL mark documents as active or inactive
5. WHEN a document is marked inactive, THE Knowledge_Base SHALL exclude it immediately from all retrieval operations
6. THE Knowledge_Base SHALL preserve the relationship between document chunks and their source documents

### Requirement 7: Document Ingestion and Processing

**User Story:** As a support staff member, I want to add new institutional documents to the knowledge base, so that the system can answer questions using the latest information.

#### Acceptance Criteria

1. THE Knowledge_Base SHALL accept documents in PDF, HTML, Markdown, and plain text formats
2. WHEN a document is ingested, THE Knowledge_Base SHALL extract text content while preserving section structure
3. AFTER a document is ingested, THE Knowledge_Base SHALL divide the document into semantic chunks of 200 to 800 words with 50-word overlap between adjacent chunks
4. THE Knowledge_Base SHALL enrich each chunk with metadata identifying the source document, section title, page number, and effective date
5. THE Knowledge_Base SHALL generate embedding vectors for each chunk using a consistent embedding model
6. THE Knowledge_Base SHALL store chunks and embeddings in a vector database for semantic retrieval

### Requirement 8: Knowledge Retrieval with Source Priority

**User Story:** As the system, I want to retrieve the most relevant and authoritative institutional information, so that responses are grounded in approved sources.

#### Acceptance Criteria

1. WHEN the RAG_Service receives a classified Student_Email, THE RAG_Service SHALL generate a semantic query from the student's question
2. THE RAG_Service SHALL retrieve the top 10 most semantically similar chunks from the Knowledge_Base
3. THE RAG_Service SHALL rank retrieved chunks by relevance score
4. THE RAG_Service SHALL assign higher priority to current official policy documents than historical documents
5. THE RAG_Service SHALL assign higher priority to official handbooks than general website content
6. THE RAG_Service SHALL return chunks with relevance scores of 0.70 or higher including chunks scoring exactly 0.70
7. WHEN no chunks score 0.70 or higher, THE RAG_Service SHALL return an empty result set indicating insufficient knowledge

### Requirement 9: Grounded Response Generation

**User Story:** As a support staff member, I want the system to generate answers based only on approved sources, so that students do not receive invented or unsupported information.

#### Acceptance Criteria

1. WHEN the Response_Generator receives retrieved chunks from the RAG_Service, THE Response_Generator SHALL create a draft email response using only the provided evidence
2. THE Response_Generator SHALL structure responses with acknowledgment, direct answer, relevant next steps, and source references
3. THE Response_Generator SHALL cite the source document title and section when providing answers
4. THE Response_Generator SHALL maintain a professional and concise tone appropriate for institutional email communication
5. WHEN insufficient evidence exists to answer the student's question, THE Response_Generator SHALL decline to generate a response and automatically mark the request for escalation
6. THE Response_Generator SHALL avoid inventing dates, deadlines, contact information, or policy details not present in retrieved chunks

### Requirement 10: Response Validation and Safety Checks

**User Story:** As a support staff member, I want responses validated before they are sent, so that students receive correct and safe information.

#### Acceptance Criteria

1. WHEN the Response_Validator receives a draft response, THE Response_Validator SHALL verify that the answer addresses the student's question
2. WHEN any validation check fails, THE Response_Validator SHALL reject the entire response
3. THE Response_Validator SHALL verify that all factual claims are supported by retrieved evidence
4. THE Response_Validator SHALL verify that dates, deadlines, and contact information are correct and current
5. THE Response_Validator SHALL detect unsupported claims not present in the Knowledge_Base
6. THE Response_Validator SHALL detect potential disclosure of confidential information
7. THE Response_Validator SHALL detect responses that contradict known institutional policies
8. WHEN the Response_Validator detects a validation failure, THE Response_Validator SHALL reject the response, block the response from being sent, and mark the request for human review

### Requirement 11: Conversation Thread Management

**User Story:** As the system, I want to maintain conversation context across multiple emails, so that follow-up questions are understood correctly.

#### Acceptance Criteria

1. THE Support_Agent SHALL group emails by Gmail thread ID into Conversation_Threads
2. WHEN a Student_Email belongs to an existing Conversation_Thread, THE Support_Agent SHALL retrieve previous messages and AI responses from that thread
3. THE Triage_Service SHALL interpret follow-up questions in the context of the previous conversation
4. THE RAG_Service SHALL consider previous retrieved documents when processing follow-up questions
5. THE Support_Agent SHALL maintain conversation state including previous classification, escalation status, and resolution mode
6. WHEN a previously resolved Conversation_Thread receives a new Student_Email, THE Support_Agent SHALL attempt to reopen the conversation
7. IF the reopening mechanism fails, THE Support_Agent SHALL queue the request for manual intervention and alert administrators

### Requirement 12: Automated Response Sending

**User Story:** As a student, I want to receive quick answers to routine questions, so that I can proceed without waiting for human staff availability.

#### Acceptance Criteria

1. WHERE automatic responses are enabled for a request category, WHEN Resolution_Mode is AUTO_REPLY and the Response_Validator approves the response, THE Support_Agent SHALL send the response email within 5 minutes of receiving the Student_Email
2. THE Support_Agent SHALL send responses using the monitored support mailbox as the sender
3. THE Support_Agent SHALL maintain the Gmail thread by replying to the original thread ID
4. THE Support_Agent SHALL apply the label "AI-AUTO-ANSWERED" to the Gmail thread after sending
5. THE Support_Agent SHALL record the sent response with timestamp, generated content, and retrieved sources in the conversation history

### Requirement 13: Human Review Workflow

**User Story:** As a support staff member, I want to review and approve AI-generated responses before they are sent, so that I can ensure quality for medium-confidence cases.

#### Acceptance Criteria

1. WHEN Resolution_Mode is HUMAN_REVIEW, THE Support_Agent SHALL add the draft response to the Approval_Queue
2. THE Support_Agent SHALL apply the label "AI-HUMAN-REVIEW" to the Gmail thread
3. THE Support_Agent SHALL present the draft response with retrieved sources, confidence scores, and classification metadata to Support_Staff via the Admin_Dashboard
4. THE Support_Staff SHALL be able to approve, edit and approve, or reject the draft response
5. WHEN Support_Staff approves a draft, THE Support_Agent SHALL send the response within 2 minutes
6. IF sending fails within 2 minutes, THE Support_Agent SHALL escalate the request to manual processing or retry with extended timeouts
7. WHEN Support_Staff edits and approves a draft, THE Support_Agent SHALL send the edited version
8. WHEN Support_Staff rejects a draft, THE Support_Agent SHALL mark the request for manual handling

### Requirement 14: Escalation Workflow

**User Story:** As a support staff member, I want complex and sensitive cases routed to me directly, so that students receive appropriate institutional judgment.

#### Acceptance Criteria

1. WHEN Resolution_Mode is ESCALATE, THE Support_Agent SHALL add the request to the Escalation_Queue
2. THE Support_Agent SHALL apply the label "AI-ESCALATED" to the Gmail thread
3. THE Support_Agent SHALL generate a concise summary including student name, topic, urgency, sensitivity, escalation reason, and relevant context
4. THE Support_Agent SHALL present escalated requests with priority ordering based on urgency via the Admin_Dashboard
5. THE Support_Agent SHALL notify assigned Support_Staff of new escalations within 5 minutes
6. THE Support_Agent SHALL mark escalated requests as awaiting human intervention

### Requirement 15: Interaction Logging and Audit Trail

**User Story:** As a support staff member, I want to see what the system did for each request, so that I can review automated decisions and understand past interactions.

#### Acceptance Criteria

1. THE Support_Agent SHALL log each Student_Email with timestamp, sender, subject, body, and thread ID
2. THE Support_Agent SHALL log each classification decision with intent, urgency, sensitivity, Confidence_Score, and Resolution_Mode
3. THE Support_Agent SHALL log each retrieval operation with query, retrieved chunks, relevance scores, and source documents
4. THE Support_Agent SHALL log each generated response with draft content, validation result, and approval status
5. THE Support_Agent SHALL log each sent response with final content, timestamp, and delivery status
6. THE Support_Agent SHALL maintain logs for 2 years for audit and improvement purposes
7. THE Support_Agent SHALL allow Support_Staff to view complete interaction history for any Conversation_Thread via the Admin_Dashboard

### Requirement 16: Admin Dashboard and Operational Visibility

**User Story:** As a support staff member, I want to see real-time system status and statistics, so that I can monitor performance and workload.

#### Acceptance Criteria

1. THE Admin_Dashboard SHALL display the count of requests received today
2. THE Admin_Dashboard SHALL display the count of requests automatically answered, in human review, and escalated today
3. THE Admin_Dashboard SHALL display average response time for automatic responses
4. THE Admin_Dashboard SHALL display the distribution of requests by topic category
5. THE Admin_Dashboard SHALL display current Confidence_Score distribution
6. THE Admin_Dashboard SHALL display escalation rate percentage
7. THE Admin_Dashboard SHALL provide access to the Approval_Queue and Escalation_Queue
8. THE Admin_Dashboard SHALL refresh statistics every 5 minutes
9. THE Admin_Dashboard SHALL allow Support_Staff to search and filter conversations by date, student, topic, or status

### Requirement 17: Knowledge Gap Detection

**User Story:** As a support staff member, I want to identify questions the system cannot answer confidently, so that I can improve documentation.

#### Acceptance Criteria

1. WHEN the RAG_Service returns insufficient evidence for any request, THE Support_Agent SHALL generate a knowledge gap alert
2. WHEN the RAG_Service returns insufficient evidence with a Confidence_Score of 0.00, THE Support_Agent SHALL generate a knowledge gap alert
3. WHEN a question type with insufficient evidence occurs at least 5 times within 30 days, THE Support_Agent SHALL include occurrence count in the knowledge gap alert
4. THE knowledge gap alert SHALL include the topic, occurrence count when applicable, average Confidence_Score, and sample student questions
5. THE Support_Agent SHALL create the knowledge gap alert immediately even without generating a recommendation for Knowledge_Base updates
6. THE Admin_Dashboard SHALL display active knowledge gap alerts

### Requirement 18: Staff Feedback Collection

**User Story:** As a support staff member, I want to provide feedback on AI responses, so that the system can improve over time.

#### Acceptance Criteria

1. THE Admin_Dashboard SHALL allow Support_Staff to mark AI responses as correct, incorrect, unclear, too long, missing information, wrong source, wrong classification, should have escalated, or should not have escalated
2. WHEN Support_Staff provides feedback, THE Support_Agent SHALL attempt to record the feedback type, original response, corrected response if provided, and timestamp
3. IF feedback recording fails, THE Support_Agent SHALL proceed without retry or notification
4. THE Support_Agent SHALL associate feedback with the corresponding conversation, classification, and retrieved sources
5. THE Admin_Dashboard SHALL display feedback statistics aggregated by topic category and resolution mode

### Requirement 19: Security and Access Control

**User Story:** As a system administrator, I want to ensure that only authorized staff can access student communications and system functions, so that student privacy is protected.

#### Acceptance Criteria

1. THE Support_Agent SHALL authenticate all Admin_Dashboard users using secure authentication
2. THE Support_Agent SHALL require role-based permissions for accessing the Approval_Queue, Escalation_Queue, conversation history, and system configuration uniformly for all staff with the same role
3. THE Support_Agent SHALL encrypt all student email content and conversation data at rest
4. THE Support_Agent SHALL encrypt all data in transit using TLS 1.2 or higher
5. WHEN logging of Support_Staff access to student conversations fails, THE Support_Agent SHALL block access entirely
6. THE Support_Agent SHALL log all Support_Staff access to student conversations with user ID, timestamp, and action performed
7. THE Support_Agent SHALL maintain access logs for 2 years

### Requirement 20: Prompt Injection Protection

**User Story:** As a system administrator, I want the system to treat student email content as untrusted data, so that malicious instructions in emails do not compromise system behavior.

#### Acceptance Criteria

1. THE Support_Agent SHALL treat all Student_Email content as data to be analyzed rather than system instructions
2. THE Support_Agent SHALL separate system instructions, application policy, Knowledge_Base content, and student-provided content in distinct processing contexts
3. WHEN a Student_Email contains instructions attempting to override system behavior, THE Support_Agent SHALL ignore those instructions and process the email normally
4. THE Response_Generator SHALL not execute commands, reveal system prompts, or disclose internal configuration based on Student_Email content

### Requirement 21: Configuration and Automation Control

**User Story:** As a system administrator, I want to control which request categories can be answered automatically, so that automation can be enabled gradually as performance is proven.

#### Acceptance Criteria

1. THE Support_Agent SHALL maintain a configuration specifying which topic categories are enabled for AUTO_REPLY mode
2. THE Support_Agent SHALL default all categories to HUMAN_REVIEW mode until explicitly enabled for automation
3. THE system administrator SHALL be able to enable or disable AUTO_REPLY mode for each topic category independently
4. WHEN a category is disabled for automation, THE Support_Agent SHALL block auto-reply and set Resolution_Mode to HUMAN_REVIEW for requests in that category regardless of Confidence_Score
5. THE Support_Agent SHALL apply configuration changes within 5 minutes of update

### Requirement 22: Daily Summary Reports

**User Story:** As a support staff member, I want to receive daily summaries of system activity, so that I understand workload and system performance without manually checking the dashboard.

#### Acceptance Criteria

1. THE Support_Agent SHALL generate a daily summary report at 08:00 local time each day
2. THE daily summary SHALL include total conversations, automatically resolved count, human review count, escalated count, most common topics, and notable issues
3. THE daily summary SHALL include a list of knowledge gaps detected in the past 24 hours
4. THE daily summary SHALL include a list of conversations requiring urgent attention
5. WHEN some sections fail to generate, THE Support_Agent SHALL send a partial report with available sections and note the missing data
6. THE Support_Agent SHALL deliver the daily summary report via email to configured Support_Staff recipients

### Requirement 23: Parser for Institutional Documents

**User Story:** As a support staff member, I want the system to reliably extract structured information from institutional documents, so that the Knowledge_Base accurately represents official resources.

#### Acceptance Criteria

1. WHEN the Knowledge_Base ingests a structured document, THE Document_Parser SHALL parse it according to the document's format grammar
2. WHEN the Document_Parser encounters an invalid document, THE Document_Parser SHALL return a descriptive error identifying the parsing failure location
3. THE Pretty_Printer SHALL format parsed document structures back into valid document files in the original format
4. FOR ALL valid parsed documents, parsing with Document_Parser then formatting with Pretty_Printer then parsing again SHALL produce an equivalent document structure (round-trip property)
5. THE Document_Parser SHALL preserve section hierarchy, headings, and metadata during parsing

