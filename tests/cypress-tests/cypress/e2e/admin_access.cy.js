// cypress/e2e/admin_access.cy.js

describe("Admin Access Protection", () => {
    it("should block access to admin dashboard without login", () => {
      cy.visit("/admin-panel");
      cy.on("window:alert", (txt) => {
        expect(txt).to.contains("You must login as admin.");
      });
      cy.url().should("include", "/admin-login");
    });
  
    it("should show error on wrong password", () => {
      cy.visit("/admin");
      cy.get("input[type='password']").type("wrongpassword");
      cy.contains("🔓 Login").click();
      cy.contains("❌ Incorrect password.");
      cy.url().should("include", "/admin");
    });
  
    it("should allow access with correct admin password", () => {
      cy.visit("/admin");
      cy.get("input[type='password']").type("admin1");
      cy.contains("🔓 Login").click();
      cy.url().should("include", "/admin-panel");
      cy.contains("📊 Admin Dashboard");
    });
  });
  