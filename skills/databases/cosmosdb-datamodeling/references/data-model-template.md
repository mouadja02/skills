# Final deliverable: cosmosdb_data_model.md

Moved verbatim from SKILL.md so the entry file stays small.

### Final Deliverable: cosmosdb_data_model.md

Creation Trigger: Only after USER confirms all access patterns captured and validated
Purpose: Step-by-step reasoned final design with complete justifications

📋 Template for cosmosdb_data_model.md:

```markdown
# Azure Cosmos DB NoSQL Data Model

## Design Philosophy & Approach
[Explain the overall approach taken and key design principles applied, including aggregate-oriented design decisions]

## Aggregate Design Decisions
[Explain how you identified aggregates based on access patterns and why certain data was grouped together or kept separate]

## Container Designs

🔴 **CRITICAL**: You MUST group indexes with the containers they belong to.

### [ContainerName] Container

A JSON representation showing 5-10 representative documents for the container

```json
[
  {
    "id": "user_123",
    "partitionKey": "user_123",
    "type": "user",
    "name": "John Doe",
    "email": "john@example.com"
  },
  {
    "id": "order_456", 
    "partitionKey": "user_123",
    "type": "order",
    "userId": "user_123",
    "amount": 99.99
  }
]
```

- **Purpose**: [what this container stores and why this design was chosen]
- **Aggregate Boundary**: [what data is grouped together in this container and why]
- **Partition Key**: [field] - [detailed justification including distribution reasoning, whether it's an identifying relationship and if so why]
- **Document Types**: [list document type patterns and their semantics; e.g., `user`, `order`, `payment`]
- **Attributes**: [list all key attributes with data types]
- **Access Patterns Served**: [Pattern #1, #3, #7 - reference the numbered patterns]
- **Throughput Planning**: [RU/s requirements and autoscale strategy]
- **Consistency Level**: [Session/Eventual/Strong - with justification]

### Indexing Strategy
- **Indexing Policy**: [Automatic/Manual - with justification]
- **Included Paths**: [specific paths that need indexing for query performance]
- **Excluded Paths**: [paths excluded to reduce RU consumption and storage]
- **Composite Indexes**: [multi-property indexes for ORDER BY and complex filters]
  ```json
  {
    "compositeIndexes": [
      [
        { "path": "/userId", "order": "ascending" },
        { "path": "/timestamp", "order": "descending" }
      ]
    ]
  }
  ```
- **Access Patterns Served**: [Pattern #2, #5 - specific pattern references]
- **RU Impact**: [expected RU consumption and optimization reasoning]

## Access Pattern Mapping
### Solved Patterns

🔴 CRITICAL: List both writes and reads solved.

## Access Pattern Mapping

[Show how each pattern maps to container operations and critical implementation notes]

| Pattern | Description | Containers/Indexes | Cosmos DB Operations | Implementation Notes |
|---------|-----------|---------------|-------------------|---------------------|

## Hot Partition Analysis
- **MainContainer**: Pattern #1 at 500 RPS distributed across ~10K users = 0.05 RPS per partition ✅
- **Container-2**: Pattern #4 filtering by status could concentrate on "ACTIVE" status - **Mitigation**: Add random suffix to partition key

## Trade-offs and Optimizations

[Explain the overall trade-offs made and optimizations used as well as why - such as the examples below]

- **Aggregate Design**: Kept Orders and OrderItems together due to 95% access correlation - trades document size for query performance
- **Denormalization**: Duplicated user name in Order document to avoid cross-partition lookup - trades storage for performance  
- **Normalization**: Kept User as separate document type from Orders due to low access correlation (15%) - optimizes update costs
- **Indexing Strategy**: Used selective indexing instead of automatic to balance cost vs additional query needs
- **Multi-Document Containers**: Used multi-document containers for [access_pattern] to enable transactional consistency

## Global Distribution Strategy

- **Multi-Region Setup**: [regions selected and reasoning]
- **Consistency Levels**: [per-operation consistency choices]
- **Conflict Resolution**: [policy selection and custom resolution procedures]
- **Regional Failover**: [automatic vs manual failover strategy]

## Validation Results 🔴

- [ ] Reasoned step-by-step through design decisions, applying Important Cosmos DB Context, Core Design Philosophy, and optimizing using Design Patterns ✅
- [ ] Aggregate boundaries clearly defined based on access pattern analysis ✅
- [ ] Every access pattern solved or alternative provided ✅
- [ ] Unnecessary cross-partition queries eliminated using identifying relationships ✅
- [ ] All containers and indexes documented with full justification ✅
- [ ] Hot partition analysis completed ✅
- [ ] Cost estimates provided for high-volume operations ✅
- [ ] Trade-offs explicitly documented and justified ✅
- [ ] Global distribution strategy detailed ✅
- [ ] Cross-referenced against `cosmosdb_requirements.md` for accuracy ✅
```
