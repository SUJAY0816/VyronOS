# VYRONOS — AGENT RULES AND ARCHITECTURAL POLICIES

## TARGET ENVIRONMENT & VIRTUALIZATION
- Oracle VM VirtualBox exclusively (Darwin ARM64 / Apple Silicon).
- Zero QEMU configurations, commands, or runtime dependencies.

# VYRONOS — ORIGINALITY, INDEPENDENT IDENTITY & PROVENANCE POLICY

## Core Objective

VyronOS must develop a distinct operating-system identity. It must not be a superficial rebranding exercise that simply changes another distribution's wallpaper, logo, theme and desktop panel.

The objective is to build an original, cohesive, recognizable operating-system product.

## 1. Original User Experience

Develop Vyron-specific implementations and experiences wherever technically feasible:

- Original boot and login experience.
- Original desktop identity and interaction design.
- Original launcher and application navigation.
- Original settings and system control interface.
- Original iconography, wallpapers and visual assets.
- Original system utilities and configuration tools.
- Original installer and first-boot experience.
- Consistent typography, spacing, colors, animations and interaction patterns.

## 2. No Misleading Branding

Do not expose unrelated distribution branding as Vyron branding.

Remove inherited logos, wallpapers, welcome messages, menu labels and unnecessary third-party visual identities from the Vyron user-facing experience, where legally and technically appropriate.

Do not falsely claim that third-party components are independently developed.

## 3. Original Implementation

Before introducing a component, investigate whether it can be independently implemented or substantially redesigned.

Do not blindly copy complete desktop environments, themes, scripts, icons, applications or configuration bundles and present them as original Vyron work.

Third-party software may be used when appropriate, but its provenance, license and modifications must be documented.

## 4. Legal and Technical Transparency

VyronOS must retain all required copyright notices, license texts, attribution and third-party acknowledgements.

Document the actual Linux kernel, Debian base, package origins and upstream dependencies.

Never remove mandatory licensing information or make false claims about the origin of underlying software.

## 5. Component Provenance Registry

Maintain a registry for every significant component with:

- Component name.
- Original developer or upstream project.
- License.
- Source repository.
- Modifications made by Vyron.
- Whether the component is original, customized or upstream.
- Required attribution.

## 6. Acceptance Criteria

A component is not considered Vyron-original merely because its name, icon or colors have changed.

Evaluate originality based on actual implementation, interaction design, functionality, visual identity and documented provenance.

## 7. Release Requirement

Before production release, perform a branding and provenance audit.

Verify that:

- No unintended third-party branding remains in the user interface.
- Original Vyron assets are distinguishable from upstream assets.
- Required licensing and attribution are preserved.
- Documentation accurately describes the technical foundations.
- No false independent-development claims are made.

This policy applies to all future VyronOS phases and releases.
