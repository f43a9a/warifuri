# Security Policy

## Supported Versions

We actively maintain and provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Security Features

warifuri implements several security measures:

- **Dependency Scanning**: Automated vulnerability scanning with Dependabot
- **Static Analysis**: CodeQL analysis for security vulnerabilities
- **Code Quality**: Bandit security linting for Python code
- **Safe Defaults**: Secure configuration defaults and input validation
- **Minimal Permissions**: Least-privilege principle for GitHub API access

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

### 🔒 Private Disclosure (Preferred)

1. **DO NOT** create a public GitHub issue for security vulnerabilities
2. Use GitHub's private vulnerability reporting feature:
   - Go to the [Security tab](https://github.com/f43a9a/warifuri/security)
   - Click "Report a vulnerability"
   - Provide detailed information about the vulnerability

### 📧 Alternative Contact

If you cannot use GitHub's security reporting, email us at:
- **Primary**: security@warifuri.example.com (replace with actual email)
- **Backup**: f43a9a@example.com (replace with actual email)

### 📋 What to Include

Please include the following information:

- **Description**: Clear description of the vulnerability
- **Impact**: Potential impact and affected components
- **Reproduction**: Step-by-step instructions to reproduce
- **Environment**: Operating system, Python version, warifuri version
- **Proof of Concept**: Code or commands that demonstrate the issue
- **Suggested Fix**: If you have ideas for fixing the vulnerability

### 🕒 Response Timeline

We commit to the following response times:

| Severity | Initial Response | Status Update | Resolution Target |
|----------|------------------|---------------|-------------------|
| Critical | 24 hours         | 48 hours      | 7 days            |
| High     | 48 hours         | 72 hours      | 14 days           |
| Medium   | 5 days           | 1 week        | 30 days           |
| Low      | 1 week           | 2 weeks       | 60 days           |

### 🎯 Vulnerability Assessment

We classify vulnerabilities using the following criteria:

#### Critical
- Remote code execution
- Authentication bypass
- Privilege escalation to admin/root
- Data exfiltration of sensitive information

#### High
- Local privilege escalation
- Denial of service affecting availability
- Information disclosure of sensitive data
- Cross-site scripting (if applicable)

#### Medium
- Information disclosure of non-sensitive data
- Local denial of service
- Input validation bypass

#### Low
- Information leakage with minimal impact
- Minor configuration issues
- Non-exploitable code quality issues

### 🛡️ Security Best Practices for Users

To use warifuri securely:

1. **Keep Updated**: Always use the latest version
2. **GitHub Tokens**: Use fine-grained personal access tokens with minimal permissions
3. **Environment Variables**: Store sensitive configuration in environment variables
4. **File Permissions**: Ensure configuration files have appropriate permissions
5. **Network Security**: Use HTTPS for all GitHub API communication
6. **Input Validation**: Validate all user inputs and configuration

### 🏆 Recognition

We believe in recognizing security researchers who help keep warifuri secure:

- **Public Thanks**: With your permission, we'll acknowledge your contribution
- **CVE Assignment**: For qualifying vulnerabilities, we'll request CVE assignment
- **Security Advisory**: We'll publish security advisories for significant issues

### 📚 Resources

- [GitHub Security Guidelines](https://docs.github.com/en/code-security)
- [Python Security Best Practices](https://python.org/dev/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

---

Thank you for helping keep warifuri and its users safe! 🔒
