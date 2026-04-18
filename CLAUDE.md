# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**compound-practice** is a multi-project repository for practicing software engineering patterns and domain-driven design. Two main projects are included:

1. **json-cli/** — A simple practice project implementing CRUD operations on JSON files using Typer CLI
2. **kiosk/** — A domain-driven design (DDD) implementation of a self-service kiosk ordering system with cart functionality, menu management, order processing, and payment handling

The repository also includes a sophisticated development workflow powered by the "mini-harness" system: a hook-based orchestration chain combining council debates, task specification, dependency resolution, and learning capture.

---

## Quick Start

### Prerequisites

- Python 3.8+
- pytest (for testing)
- typer (for json-cli only)

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_order.py

# Single test
pytest tests/test_order.py::test_order_creation

# With coverage
pytest --cov=kiosk tests/
```

### Running Projects

**json-cli:**
```bash
cd json-cli
pip install typer
python cli.py list-tasks
```

**kiosk CLI:**
```bash
cd kiosk
python cli.py
```

---

## Architecture: Kiosk System (DDD)

The kiosk project follows Domain-Driven Design with clear separation of concerns:

### Layer Structure

**domain/** — Business logic and rules
- `models/` — Core entities and value objects (Order, MenuItem, Payment, etc.)
- `services/` — Domain services containing cross-aggregate logic (OrderDomainService)
- `repositories/` — Repository interfaces (no implementation)

**application/** — Use cases and workflows
- `use_cases/` — Application logic that orchestrates domain models and repositories
  - Single Responsibility: each use case handles one business operation
  - Dependency injection via constructor
  - Return DTOs instead of domain models

**infrastructure/** — Implementation details
- `repositories/` — Concrete repository implementations (currently in-memory)
- `seed_data.py` — Initial data for in-memory repositories

### Key Design Patterns

**Value Objects** (frozen dataclasses):
- Immutable, identity-less objects representing concepts like Money, Quantity, MenuItemId
- Located in `domain/models/value_objects.py`
- When mutable state change is needed (e.g., cart quantity update), use `object.__setattr__()` internally with invariant validation (see `.mini-harness/learnings/2026-04-18-frozen-dataclass-mutation.md`)

**Aggregates**:
- `Order` — Root aggregate managing order items and state transitions (PENDING → CONFIRMED → PAID)
- `MenuItem` — Simple entity with no sub-aggregates
- `Payment` — Tracks payment status and method

**Repository Pattern**:
- Domain defines interfaces in `domain/repositories/`
- Infrastructure provides in-memory implementations
- Enables easy testing and future database migration

### Domain Model: Order State Machine

The Order aggregate manages three states:
- **PENDING** — Items added to cart (not yet committed)
- **CONFIRMED** — Cart converted to order (ready for payment)
- **PAID** — Payment successful

```python
Order.add_item(menu_item_id, quantity)  # PENDING state only
Order.confirm()  # Transition to CONFIRMED
Order.mark_paid()  # Transition to PAID
```

**Important**: When the same menu item is added twice to a PENDING order, the quantity increases (not a duplicate line item). This is enforced in the domain model.

---

## Common Development Tasks

### Adding a New Use Case

1. Create file in `kiosk/application/use_cases/`
2. Import dependencies (repositories, domain services)
3. Accept repositories and services in `__init__`
4. Implement `execute(...)` method returning a DTO
5. Add corresponding test in `tests/test_use_cases.py`
6. Wire up in `kiosk/cli.py` dependency container (`build_dependencies()`)

Example:
```python
class MyUseCase:
    def __init__(self, order_repo, domain_service):
        self.order_repo = order_repo
        self.domain_service = domain_service
    
    def execute(self, param1, param2):
        # Orchestrate domain logic
        order = self.order_repo.get(...)
        order.some_operation()
        self.order_repo.save(order)
        return MyDTO(...)  # Return DTO, not domain model
```

### Adding a Domain Value Object

1. Define in `kiosk/domain/models/value_objects.py` as a frozen dataclass
2. Include validation in `__post_init__`
3. Add type hint to relevant entities
4. Test invariants in `tests/test_value_objects.py`

### Running the CLI

The kiosk CLI is interactive. Start with:
```bash
cd kiosk
python cli.py
```

Menu options:
1. Add item to cart (specifies order ID)
2. Update quantity
3. Remove item
4. View cart
5. Checkout (transitions to CONFIRMED)
6. Process payment (transitions to PAID)

---

## Testing Strategy

### Test Structure

- **Unit tests** (`test_*.py`): Test domain models, value objects, and individual use cases in isolation
- **Integration tests** (`test_*_integration.py`): Test workflows across multiple use cases
- `conftest.py`: Shared fixtures (repositories, domain services)

### Key Fixtures

```python
@pytest.fixture
def order_repo():
    return InMemoryOrderRepository()

@pytest.fixture
def menu_repo():
    return InMemoryMenuItemRepository()
```

### Testing Patterns

Use `conftest.py` for shared setup. Mock repositories are provided by InMemory implementations; no external mocks needed.

Example test:
```python
def test_add_item_to_cart(order_repo, menu_repo):
    # Arrange
    menu = menu_repo.get_all()[0]
    
    # Act
    cart = AddToCartUseCase(order_repo).execute("", str(menu.id.value), menu.name, "5000", 2)
    
    # Assert
    assert cart.item_count == 2
    assert cart.total_amount == "10000"
```

---

## Mini-Harness Development Workflow

The project includes a sophisticated hook-based orchestration system (`mini-harness`) for structured decision-making and learning capture.

### Workflow Chain

```
/mini-harness [goal]
  ↓
/council [topic]          (Debate → ADR)
  ↓
/mini-specify [goal]      (Search learnings, output task list)
  ↓
/taskify                  (Break requirements into structured tasks)
  ↓
/dependency-resolve       (Analyze task dependencies)
  ↓
/mini-execute             (Implement each task, capture friction)
  ↓
/mini-compound            (Promote learnings.json to permanent .md files)
```

### How to Use

1. **Start a structured decision**: `/mini-harness [goal]`
   - Triggers the full learning loop via Stop hooks
   - Each phase feeds into the next

2. **Debate an architectural decision**: `/council [topic]`
   - Spawns a 4-panel team (UX/tech/product/devil's advocate)
   - Runs 2-phase debate (positions → rebuttal)
   - Outputs ADR to `.dev/adr/`

3. **Implement tasks**: `/mini-execute`
   - Reads `.dev/task/spec.json`
   - Iterates over tasks, implementing each
   - Records friction/learnings to `session/learnings.json`

### Key Files

- `.dev/requirements/requirements.json` — Business requirements
- `.dev/task/spec.json` — Structured task breakdown (output of /taskify)
- `.dev/adr/` — Architecture decision records
- `.mini-harness/learnings/` — Reusable patterns and rules discovered during development
- `session/learnings.json` — Current session friction logs (merged to .mini-harness/ on /mini-compound)

### Learnings System

Learnings capture non-obvious rules discovered during implementation:
- **DDD patterns**: frozen dataclass mutation strategies
- **Repository patterns**: when to use dependency injection dicts
- **Testing approaches**: repository interface consistency

Access learnings during planning with `/mini-specify` — it searches the `learnings/` directory before generating task lists.

---

## Code Organization & Naming

### Directories

```
kiosk/
  __init__.py
  cli.py                      # Interactive CLI entry point
  domain/
    __init__.py
    models/
      __init__.py
      menu_item.py            # MenuItem entity
      order.py                # Order aggregate root
      payment.py              # Payment entity
      value_objects.py        # Immutable value objects (Money, Quantity, etc.)
    repositories/
      __init__.py
      menu_item_repository.py # Interface
      order_repository.py     # Interface
      payment_repository.py   # Interface
    services/
      __init__.py
      order_domain_service.py # Cross-aggregate logic
  application/
    __init__.py
    use_cases/
      __init__.py
      get_menu.py
      place_order.py
      process_payment.py
      cart_use_cases.py       # AddToCart, RemoveFromCart, UpdateQuantity, ViewCart, Checkout
  infrastructure/
    __init__.py
    repositories/
      __init__.py
      in_memory_*.py          # Concrete implementations
    seed_data.py              # Initial data
```

### Naming Conventions

- **Entities/Aggregates**: PascalCase (Order, MenuItem, Payment)
- **Value Objects**: PascalCase with suffix (Money, Quantity, MenuItemId)
- **DTOs**: PascalCase with "DTO" suffix or plain PascalCase for response objects (CartDTO, PaymentDTO)
- **Use Cases**: PascalCase with "UseCase" suffix (AddToCartUseCase)
- **Services**: PascalCase with "Service" suffix (OrderDomainService)
- **Repositories**: PascalCase with "Repository" suffix, implementation with prefix (InMemoryOrderRepository)

---

## Important Constraints & Patterns

### Order State Transitions

Order follows a strict state machine:
1. Create as PENDING (implicit on first item addition)
2. Only PENDING orders accept `add_item` / `remove_item`
3. Call `confirm()` to transition to CONFIRMED
4. Call `mark_paid()` to transition to PAID

Attempting invalid operations raises `ValueError` with clear messages.

### Item Quantity Limits

Quantity must be between 1 and 10 (enforced in Quantity value object). Attempting to set outside this range raises `ValueError`.

### Cart as PENDING Order

The "cart" in the UI is not a separate entity — it's a PENDING Order aggregate. This design choice minimizes duplication and simplifies state management. See `.dev/adr/2026-04-18-order-and-shopping-cart-inclusion.md` for the full rationale.

### Dependency Injection Pattern

Dependencies are injected via constructor in use cases. The CLI layer (`kiosk/cli.py`) maintains a `build_dependencies()` function that creates all instances. Update this function when adding new repositories or use cases.

```python
def build_dependencies():
    # Create repositories
    menu_repo = InMemoryMenuItemRepository()
    order_repo = InMemoryOrderRepository()
    
    # Create services
    domain_service = OrderDomainService()
    
    # Create use cases
    get_menu = GetMenuUseCase(menu_repo)
    add_to_cart = AddToCartUseCase(order_repo)
    
    return {
        'menu_repo': menu_repo,
        'get_menu': get_menu,
        'add_to_cart': add_to_cart,
        # ...
    }
```

---

## Decision Records

The project documents significant architectural decisions in `.dev/adr/`:
- **2026-04-18-order-and-shopping-cart-inclusion.md** — Why "cart" is a PENDING Order, not a separate entity. Includes the council debate transcript and rationale for scope constraints.

Review ADRs before proposing changes to core domain model.

---

## Debugging Tips

### Inspect Order State

```python
order = order_repo.get(order_id)
print(f"State: {order.state}")
print(f"Items: {[item.name for item in order.items]}")
print(f"Total: {order.total_amount.amount}")
```

### Test Individual Use Cases

Create fixtures in `conftest.py` and run isolated tests:
```bash
pytest tests/test_use_cases.py::test_add_to_cart -vv
```

### Trace CLI Execution

Add print statements in use case `execute()` methods or domain model operations to trace the flow.

---

## Git Workflow & Commits

This project uses structured commit messages grouped by functionality. When committing changes:

1. Stage relevant files
2. Run `/commit` skill to analyze changes and group them
3. Accept the suggested grouping or adjust as needed

Example structured commits:
```
feat(kiosk): add UpdateQuantity use case with validation
test(kiosk): add integration test for cart quantity updates
refactor(domain): extract Quantity invariant checks to value object
```

---

## Performance & Scalability Notes

- **In-memory repositories** are suitable for learning but not production
- **No persistence layer** — all data is lost on application restart
- **Single-process execution** — no concurrency issues with current in-memory design
- **CLI interaction** — blocks on user input, suitable for kiosk use case

Future extensions (database, API, multiple clients) will require evaluating these constraints.

---

## References & Further Reading

- **DDD**: See domain models in `kiosk/domain/models/` for examples of entities, value objects, and aggregates
- **Use cases**: See `kiosk/application/use_cases/` for application service patterns
- **Testing**: See `tests/` for unit and integration test examples
- **Learnings**: See `.mini-harness/learnings/` for discovered patterns (frozen dataclass mutation, repository interfaces, etc.)
