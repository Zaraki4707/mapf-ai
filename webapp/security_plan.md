# Security Remediation Plan

## Multi-Agent Path Finding Application

**Document Version:** 1.0
**Last Updated:** May 9, 2026

---

## 1. Immediate Actions (0-7 Days)

### 🔴 Issue 1: Disable Debug Mode in Production

| **Attribute** | **Details** |
|---------------|-------------|
| **Issue** | FastAPI debug mode enabled (`main.py:16`) |
| **Severity** | Critical |
| **Fix** | Set `debug=False` in production configuration |
| **Owner** | Backend Developer |

**Remediation Steps:**
1. Modify `backend/main.py` line 16:
```python
# BEFORE (VULNERABLE)
app = FastAPI(
    title=settings.app_name,
    debug=True
)

# AFTER (SECURE)
app = FastAPI(
    title=settings.app_name,
    debug=False  # Always False for production
)
```

2. Ensure environment-based configuration:
```python
# backend/main.py
import os

app = FastAPI(
    title=settings.app_name,
    debug=os.getenv("DEBUG", "false").lower() == "true"
)
```

3. Set `DEBUG=false` in production environment variables

**Verification:**
- Deploy to staging and verify error responses don't show stack traces
- Test with intentionally malformed input and confirm generic error messages

---

### 🔴 Issue 2: Restrict CORS Configuration

| **Attribute** | **Details** |
|---------------|-------------|
| **Issue** | Overly permissive CORS (`allow_origins=["*"]` with `allow_credentials=True`) |
| **Severity** | Critical |
| **Fix** | Configure specific allowed origins |
| **Owner** | Backend Developer |

**Remediation Steps:**
1. Modify `backend/main.py` lines 19-25:
```python
# BEFORE (VULNERABLE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AFTER (SECURE) - Option 1: Specific origins
ALLOWED_ORIGINS = [
    "https://your-frontend.vercel.app",
    "https://your-domain.com",
    "http://localhost:3000",  # Development only
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)
```

2. Or use environment variable for flexibility:
```python
# backend/main.py
import os

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
if not ALLOWED_ORIGINS[0]:  # Handle empty string
    ALLOWED_ORIGINS = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
```

3. Set `ALLOWED_ORIGINS` in environment variables

**Verification:**
- Test API from unauthorized domain - should be blocked
- Test from allowed origin - should work with credentials

---

### 🔴 Issue 3: Hardcoded API URL - Move to Environment Configuration

| **Attribute** | **Details** |
|---------------|-------------|
| **Issue** | Production API URL hardcoded in frontend source |
| **Severity** | Critical |
| **Fix** | Use environment variables for API URL |
| **Owner** | Frontend Developer |

**Remediation Steps:**
1. Update `frontend/.env`:
```bash
# Development
REACT_APP_API_URL=http://localhost:8000

# Production (in Vercel environment variables)
REACT_APP_API_URL=https://your-backend.vercel.app
```

2. Update `frontend/src/App.js`:
```javascript
// BEFORE (VULNERABLE)
const API_URL = 'https://backend-taupe-gamma-78.vercel.app';

// AFTER (SECURE)
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

3. Update `frontend/src/components/InputForm.js` similarly:
```javascript
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

4. Configure environment variables in Vercel dashboard

**Verification:**
- Check built JavaScript contains no hardcoded URLs
- Verify API calls go to correct environment URL

---

## 2. Short-term Improvements (1-4 Weeks)

### 🟠 Issue 4: Remove Source Maps from Production

| **Attribute** | **Details** |
|---------------|-------------|
| **Issue** | Source maps exposed in production build |
| **Severity** | High |
| **Fix** | Disable source map generation in production build |
| **Owner** | Frontend Developer |

**Remediation Steps:**
1. Update `frontend/package.json` build script:
```json
{
  "scripts": {
    "build": "GENERATE_SOURCEMAP=false react-scripts build"
  }
}
```

2. Or update `frontend/.env.production`:
```bash
GENERATE_SOURCEMAP=false
```

3. Rebuild and verify no `.map` files exist in build output:
```bash
npm run build
ls -la build/static/js/
```

**Verification:**
- Confirm no `.map` files in `build/` directory
- Verify source code not accessible via browser devtools

---

### 🟠 Issue 5: Add Security Headers Middleware

| **Attribute** | **Details** |
|---------------|-------------|
| **Issue** | Missing security headers (HSTS, X-Frame-Options, etc.) |
| **Severity** | High |
| **Fix** | Add custom security headers middleware |
| **Owner** | Backend Developer |

**Remediation Steps:**
1. Create `backend/app/middleware/security.py`:
```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # HSTS (only for HTTPS - enable in production with proper domain)
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response
```

2. Register middleware in `backend/main.py`:
```python
from app.middleware.security import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)
```

**Verification:**
- Check response headers using browser devtools or curl:
```bash
curl -I https://your-api.vercel.app/
```

---

### 🟠 Issue 6: Implement Rate Limiting

| **Attribute** | **Details** |
|---------------|-------------|
| **Issue** | No rate limiting on API endpoints |
| **Severity** | High |
| **Fix** | Add rate limiting middleware |
| **Owner** | Backend Developer |

**Remediation Steps:**
1. Install rate limiting library:
```bash
pip install slowapi
```

2. Create `backend/app/middleware/rate_limit.py`:
```python
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "retry_after": exc.detail
        }
    )
```

3. Apply to endpoints in `backend/app/routers/pathfinder.py`:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/find-path")
@limiter.limit("10/minute")  # Adjust as needed
async def find_path(request: Request, pathfinder_request: PathfinderRequest):
    # ... existing code
```

4. Register error handler in `backend/main.py`:
```python
from app.middleware.rate_limit import rate_limit_exceeded_handler

app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
```

**Verification:**
- Send >10 requests/minute to endpoint - should receive 429 response

---

### 🟠 Issue 7: Add Input Validation Upper Bounds

| **Attribute** | **Details** |
|---------------|-------------|
| **Issue** | No upper bound on grid dimensions |
| **Severity** | Medium |
| **Fix** | Add maximum constraints to prevent resource exhaustion |
| **Owner** | Backend Developer |

**Remediation Steps:**
1. Update `backend/app/models.py`:
```python
class PathfinderRequest(BaseModel):
    grid_height: Optional[int] = Field(
        default=None, 
        gt=0, 
        le=1000,  # Maximum 1000 rows
        description="Grid height (rows) - required if not using map_path"
    )
    grid_width: Optional[int] = Field(
        default=None, 
        gt=0, 
        le=1000,  # Maximum 1000 columns
        description="Grid width (columns) - required if not using map_path"
    )
    num_agents: Optional[int] = Field(
        default=None, 
        gt=0, 
        le=50,  # Already has upper bound
        description="Number of agents"
    )
```

2. Add memory estimation in endpoint:
```python
@router.post("/find-path")
async def find_path(request: PathfinderRequest):
    max_cells = 1000 * 1000  # 1 million cells max
    if request.grid_height and request.grid_width:
        if request.grid_height * request.grid_width > max_cells:
            raise HTTPException(
                status_code=400,
                detail="Grid dimensions exceed maximum allowed (1,000,000 cells)"
            )
    # ... rest of code
```

**Verification:**
- Test with grid 1000x1000 - should work
- Test with grid 2000x2000 - should return 400 error

---

### 🟠 Issue 8: Secure Error Handling

| **Attribute** | **Details** |
|---------------|-------------|
| **Issue** | Error responses expose internal details |
| **Severity** | Medium |
| **Fix** | Implement generic error responses |
| **Owner** | Backend Developer |

**Remediation Steps:**
1. Update `backend/main.py`:
```python
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log full details server-side only
    logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}", exc_info=True)
    
    # Return generic message to client
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."}
    )
```

2. Create custom exception handlers for specific error types:
```python
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request parameters"}
    )
```

**Verification:**
- Trigger an error - response should not contain stack traces or internal paths

---

## 3. Long-term Roadmap (1-3 Months)

### 🟢 Issue 9: Implement API Authentication

| **Attribute** | **Details** |
|---------------|-------------|
| **Issue** | No authentication on any API endpoint |
| **Severity** | High |
| **Fix** | Implement JWT-based authentication |
| **Owner** | Backend Developer |

**Implementation Plan:**

1. Add authentication dependencies:
```bash
pip install python-jose passlib[bcrypt] python-multipart
```

2. Create `backend/app/auth/jwt_handler.py`:
```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # Generate strong key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

3. Create `backend/app/dependencies/auth.py`:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        return {"user_id": user_id}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication")
```

4. Protect endpoints:
```python
@router.post("/find-path")
async def find_path(
    request: PathfinderRequest,
    current_user: dict = Depends(get_current_user)
):
    # ... existing code
```

5. Add login endpoint:
```python
@router.post("/auth/login")
async def login(login_request: LoginRequest):
    # Verify credentials
    # Return JWT token
```

---

### 🟢 Issue 10: Add Security Logging

| **Attribute** | **Details** |
|---------------|-------------|
| **Issue** | No security event logging |
| **Severity** | Low |
| **Fix** | Implement structured security logging |
| **Owner** | DevOps Engineer |

**Implementation:**
- Integrate with centralized logging (ELK, Datadog, etc.)
- Log authentication attempts
- Log access to sensitive endpoints
- Set up alerts for suspicious patterns

---

### 🟢 Issue 11: Implement File Upload Validation

| **Attribute** | **Details** |
|---------------|-------------|
| **Issue** | Path traversal risk in map file loading |
| **Severity** | High |
| **Fix** | Add strict path validation |
| **Owner** | Backend Developer |

**Implementation:**
```python
from pathlib import Path
import os

ALLOWED_MAP_DIR = Path(__file__).parent.parent / "maps"

def _load_map_from_file(map_path: str) -> Tuple[int, int, List[Tuple[int, int]]]:
    # Resolve to absolute path and verify it's within allowed directory
    requested_path = Path(map_path).resolve()
    
    # Prevent path traversal
    if not str(requested_path).startswith(str(ALLOWED_MAP_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Invalid map path")
    
    if not requested_path.exists():
        raise HTTPException(status_code=404, detail="Map not found")
    
    # ... rest of loading logic
```

---

## 4. Preventive Measures

### Secure Development Practices

#### Code Review Checklist

- [ ] No hardcoded secrets/credentials
- [ ] No debug code in production
- [ ] Input validation on all user inputs
- [ ] Proper error handling (no stack traces)
- [ ] Authentication checks on protected endpoints
- [ ] CORS properly configured
- [ ] No sensitive data in logs

#### Security Training Recommendations

1. **OWASP Top 10** - All developers
2. **Secure Coding in Python** - Backend team
3. **Secure Coding in JavaScript/React** - Frontend team
4. **Incident Response** - DevOps team

#### Secure Coding Guidelines

**React Frontend:**
- Never store sensitive data in localStorage
- Use HttpOnly cookies for tokens
- Sanitize user input before rendering
- Use Content Security Policy
- Disable console logging in production

**FastAPI Backend:**
- Use Pydantic for input validation
- Always validate and sanitize file paths
- Hash passwords with bcrypt/argon2
- Use strong JWT secrets (256-bit minimum)
- Implement proper rate limiting
- Use parameterized queries (no SQL concatenation)
- Log security events

---

### Automated Security Testing

#### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      
  - repo: https://github.com/trufflesecurity/trufflehog
    hooks:
      - id: trufflehog
        args: ['--regex', '--entropy=False']
        
  - repo: https://github.com/pycqa/bandit
    hooks:
      - id: bandit
        args: ['-x', '.venv']
```

#### CI/CD Pipeline Security Gates

1. **Dependency Scanning**:
   - `pip-audit` for Python
   - `npm audit` for JavaScript (with CI integration)

2. **Static Analysis**:
   - `bandit` for Python security
   - `ESLint` with security plugins for React
   - `SonarQube` for comprehensive analysis

3. **Secret Scanning**:
   - TruffleHog in CI pipeline
   - GitLeaks

4. **SAST Tools**:
   - Semgrep
   - CodeQL

#### Dependency Scanning Automation

```bash
# Python (add to CI)
pip install pip-audit
pip-audit

# JavaScript (add to CI)
npm audit --audit-level=moderate
npm outdated
```

---

### Security Monitoring

#### Runtime Application Security

- **Web Application Firewall (WAF)**: Cloudflare, AWS WAF
- **API Gateway**: Rate limiting, authentication
- **RASP**: Runtime application self-protection

#### Log Aggregation & Alerting

Recommended stack:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Datadog** for cloud-native
- **Splunk** for enterprise

Alerts to configure:
- Multiple failed authentication attempts
- Unusual API call patterns
- Large request volumes
- Error rate spikes

#### Intrusion Detection

- **Network-level**: IDS/IPS (Snort, Suricata)
- **Host-level**: OSSEC, Wazuh
- **Application-level**: ModSecurity

---

## 5. Security Hardening Checklist

### React Frontend

| Task | Status |
|------|--------|
| Input sanitization implementation | ☐ Pending |
| Secure token storage (HttpOnly cookies) | ☐ Pending |
| CSP headers configured | ☐ Pending |
| Dependencies updated | ☐ Pending |
| Source maps disabled in production | ☐ Pending |
| Environment variables secured | ☐ Pending |
| Console logging removed in production | ☐ Pending |
| No hardcoded URLs | ☐ Pending |

### FastAPI Backend

| Task | Status |
|------|--------|
| Input validation on all endpoints | ☐ Pending |
| Rate limiting implemented | ☐ Pending |
| Security headers configured | ☐ Pending |
| Database parameterized queries | N/A (no DB) |
| Password hashing with bcrypt/argon2 | ☐ Pending |
| JWT secrets rotated and strong | ☐ Pending |
| Error handling doesn't leak info | ☐ Pending |
| CORS properly configured | ☐ Pending |
| File upload restrictions | ☐ Pending |
| Logging configured securely | ☐ Pending |
| Debug mode disabled | ☐ Pending |
| Authentication implemented | ☐ Pending |

---

## 6. Tools & Resources

### Recommended Security Tools

| Category | Tool | Purpose |
|----------|------|---------|
| SAST | Bandit | Python security scanning |
| SAST | Semgrep | Multi-language security |
| SAST | CodeQL | GitHub code analysis |
| DAST | OWASP ZAP | Web vulnerability scanner |
| Dependency | pip-audit | Python vulnerability scanner |
| Dependency | npm audit | JavaScript vulnerability scanner |
| Secrets | TruffleHog | Secret detection |
| WAF | Cloudflare | DDoS & protection |
| Logging | ELK Stack | Centralized logging |

### Documentation Links

- [OWASP Top 10 2021](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [React Security Best Practices](https://reactjs.org/docs/security.html)
- [Mozilla Security Guidelines](https://wiki.mozilla.org/Security)

### Security Testing Frameworks

- OWASP Testing Guide
- NIST SP 800-53 Security Controls
- ISO 27001 Information Security

---

## 7. Success Metrics

### Vulnerability Reduction Targets

| Timeline | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Current | 3 | 5 | 5 | 2 |
| 7 Days | 0 | 2 | 4 | 2 |
| 30 Days | 0 | 0 | 2 | 2 |
| 90 Days | 0 | 0 | 0 | 0 |

### Code Coverage for Security Tests

- **Target**: 80% of security controls tested
- **Current**: 0%

### Time to Remediate by Severity

| Severity | Target MTTR |
|----------|-------------|
| Critical | < 24 hours |
| High | < 7 days |
| Medium | < 30 days |
| Low | < 90 days |

---

## 8. Conclusion

This remediation plan provides a structured approach to addressing all identified security vulnerabilities. By following this phased approach:

- **Immediate actions** (0-7 days) will eliminate the most critical risks
- **Short-term improvements** (1-4 weeks) will address high-severity issues
- **Long-term roadmap** (1-3 months) will establish a mature security posture

Regular security reviews and adherence to the preventive measures will ensure the application maintains a strong security posture going forward.

---

*Document maintained by Security Team*
*Next Review: June 9, 2026*