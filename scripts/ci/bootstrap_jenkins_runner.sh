#!/usr/bin/env bash
set -euo pipefail

BUILDER="${JENKINS_BUILDER:-acestream-builder}"
OS_RELEASE_FILE="${BOOTSTRAP_OS_RELEASE_FILE:-/etc/os-release}"
KEYRING_DIR="${BOOTSTRAP_KEYRING_DIR:-/etc/apt/keyrings}"
SOURCES_LIST_DIR="${BOOTSTRAP_SOURCES_LIST_DIR:-/etc/apt/sources.list.d}"
PREFERENCES_DIR="${BOOTSTRAP_PREFERENCES_DIR:-/etc/apt/preferences.d}"
APT_UPDATED=0
DOCKER_INSTALLED=0
SUDO=()

log() {
  printf '[bootstrap] %s\n' "$*"
}

fail() {
  printf '[bootstrap] ERROR: %s\n' "$*" >&2
  exit 1
}

have_command() {
  command -v "$1" >/dev/null 2>&1
}

current_user() {
  if have_command id; then
    id -un 2>/dev/null && return
  fi

  printf '%s\n' "${USER:-unknown-user}"
}

package_installed() {
  local status

  status="$(dpkg-query -W -f='${Status}' "$1" 2>/dev/null || true)"
  [[ "$status" == "install ok installed" ]]
}

file_has_content() {
  [[ -s "$1" ]]
}

keyring_is_valid() {
  file_has_content "$1" && gpg --show-keys "$1" >/dev/null 2>&1
}

node_major_version() {
  local version

  if ! have_command node; then
    return 1
  fi

  version="$(node --version 2>/dev/null || true)"
  version="${version#v}"
  printf '%s\n' "${version%%.*}"
}

ensure_linux() {
  if [[ "$(uname -s)" != "Linux" ]]; then
    fail "bootstrap_jenkins_runner.sh only supports Linux runners."
  fi
}

load_os_release() {
  [[ -f "$OS_RELEASE_FILE" ]] || fail "Cannot determine distro: missing $OS_RELEASE_FILE"

  # shellcheck disable=SC1090
  . "$OS_RELEASE_FILE"

  case "${ID:-}" in
    ubuntu|debian)
      ;;
    *)
      fail "Unsupported Linux distribution '${ID:-unknown}'. Only Ubuntu and Debian are supported."
      ;;
  esac

  [[ -n "${VERSION_CODENAME:-}" ]] || fail "VERSION_CODENAME is required in $OS_RELEASE_FILE"
}

require_passwordless_sudo() {
  if [[ "$EUID" -eq 0 ]]; then
    SUDO=()
    return
  fi

  if sudo -n true >/dev/null 2>&1; then
    SUDO=(sudo -n)
    return
  fi

  fail "Missing tools require installation, but passwordless sudo is unavailable for user '$(current_user)'. Grant passwordless sudo or preinstall the missing dependencies."
}

apt_update() {
  if [[ "$APT_UPDATED" -eq 0 ]]; then
    log "Running apt-get update"
    "${SUDO[@]}" apt-get update
    APT_UPDATED=1
  fi
}

install_packages() {
  local packages=("$@")

  if [[ "${#packages[@]}" -eq 0 ]]; then
    return
  fi

  require_passwordless_sudo
  apt_update
  log "Installing packages: ${packages[*]}"
  "${SUDO[@]}" apt-get install -y "${packages[@]}"
}

ensure_nodesource_repo() {
  local keyring="${KEYRING_DIR}/nodesource.gpg"
  local list_file="${SOURCES_LIST_DIR}/nodesource.list"
  local desired_line="deb [signed-by=${keyring}] https://deb.nodesource.com/node_20.x nodistro main"
  local current_line=""
  local changed=0
  local prereqs=()

  for package in ca-certificates curl gnupg; do
    if ! package_installed "$package"; then
      prereqs+=("$package")
    fi
  done

  install_packages "${prereqs[@]}"
  require_passwordless_sudo
  "${SUDO[@]}" install -m 0755 -d "$KEYRING_DIR"
  "${SUDO[@]}" install -m 0755 -d "$SOURCES_LIST_DIR"

  if ! keyring_is_valid "$keyring"; then
    log "Configuring NodeSource apt key"
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | "${SUDO[@]}" gpg --dearmor -o "$keyring"
    "${SUDO[@]}" chmod a+r "$keyring"
    changed=1
  fi

  if [[ -f "$list_file" ]]; then
    current_line="$(<"$list_file")"
  fi

  if [[ "$current_line" != "$desired_line" ]]; then
    log "Configuring NodeSource apt repository"
    printf '%s\n' "$desired_line" | "${SUDO[@]}" tee "$list_file" >/dev/null
    changed=1
  fi

  # Without a pin, apt prefers a newer distro nodejs (e.g. Ubuntu ships
  # nodejs 24 without npm) over NodeSource's node 20, so 'apt-get install
  # nodejs' becomes a no-op and npm never appears. Priority > 1000 makes
  # apt select the NodeSource build even when that is a downgrade.
  local prefs_file="${PREFERENCES_DIR}/nodesource"
  local desired_prefs=$'Package: nodejs\nPin: origin deb.nodesource.com\nPin-Priority: 1001'
  local current_prefs=""
  "${SUDO[@]}" install -m 0755 -d "$PREFERENCES_DIR"
  if [[ -f "$prefs_file" ]]; then
    current_prefs="$(<"$prefs_file")"
  fi
  if [[ "$current_prefs" != "$desired_prefs" ]]; then
    log "Configuring NodeSource apt pin"
    printf '%s\n' "$desired_prefs" | "${SUDO[@]}" tee "$prefs_file" >/dev/null
    changed=1
  fi

  if [[ "$changed" -eq 1 ]]; then
    APT_UPDATED=0
  fi
}

ensure_docker_repo() {
  local arch
  local keyring="${KEYRING_DIR}/docker.asc"
  local list_file="${SOURCES_LIST_DIR}/docker.list"
  local desired_line
  local current_line=""
  local changed=0
  local prereqs=()

  arch="$(dpkg --print-architecture)"
  desired_line="deb [arch=${arch} signed-by=${keyring}] https://download.docker.com/linux/${ID} ${VERSION_CODENAME} stable"

  for package in ca-certificates curl gnupg; do
    if ! package_installed "$package"; then
      prereqs+=("$package")
    fi
  done

  install_packages "${prereqs[@]}"
  require_passwordless_sudo
  "${SUDO[@]}" install -m 0755 -d "$KEYRING_DIR"
  "${SUDO[@]}" install -m 0755 -d "$SOURCES_LIST_DIR"

  if ! keyring_is_valid "$keyring"; then
    log "Configuring Docker apt key"
    "${SUDO[@]}" curl -fsSL "https://download.docker.com/linux/${ID}/gpg" -o "$keyring"
    "${SUDO[@]}" chmod a+r "$keyring"
    changed=1
  fi

  if [[ -f "$list_file" ]]; then
    current_line="$(<"$list_file")"
  fi

  if [[ "$current_line" != "$desired_line" ]]; then
    log "Configuring Docker apt repository"
    printf '%s\n' "$desired_line" | "${SUDO[@]}" tee "$list_file" >/dev/null
    changed=1
  fi

  if [[ "$changed" -eq 1 ]]; then
    APT_UPDATED=0
  fi
}

install_base_dependencies() {
  local -a packages=()

  if ! have_command git; then
    packages+=(git)
  fi
  if ! have_command python3; then
    packages+=(python3)
  fi
  if ! have_command rg; then
    packages+=(ripgrep)
  fi

  if have_command python3; then
    if ! python3 -m pip --version >/dev/null 2>&1; then
      packages+=(python3-pip)
    fi
    if ! python3 -m venv --help >/dev/null 2>&1; then
      packages+=(python3-venv)
    fi
  elif [[ ! " ${packages[*]} " == *" python3-pip "* ]]; then
    packages+=(python3-pip python3-venv)
  fi

  if [[ "${#packages[@]}" -gt 0 ]]; then
    install_packages "${packages[@]}"
  fi
}

install_node_if_needed() {
  local node_major

  if have_command node && have_command npm; then
    node_major="$(node_major_version || true)"
    if [[ "$node_major" == "20" ]]; then
      return
    fi
  fi

  ensure_nodesource_repo
  require_passwordless_sudo
  apt_update
  log "Installing packages: nodejs"
  # The pinned NodeSource nodejs is a downgrade relative to a newer distro
  # nodejs; apt refuses -y downgrades unless explicitly allowed.
  "${SUDO[@]}" apt-get install -y --allow-downgrades nodejs

  if ! have_command npm; then
    fail "nodejs was installed but npm is still unavailable — a distro nodejs package likely shadowed NodeSource's; check ${PREFERENCES_DIR}/nodesource and 'apt-cache policy nodejs'."
  fi
}

start_docker_with_systemctl() {
  if ! have_command systemctl; then
    return 1
  fi

  log "Enabling Docker service"
  "${SUDO[@]}" systemctl enable --now docker
}

start_docker_with_service() {
  if ! have_command service; then
    return 1
  fi

  log "Starting Docker service"
  "${SUDO[@]}" service docker start
}

ensure_docker_service() {
  local docker_info_output=""

  if ! have_command docker; then
    return
  fi

  if docker_info_output="$(docker info 2>&1)"; then
    return
  fi

  if [[ "$docker_info_output" != *"Cannot connect to the Docker daemon"* && "$docker_info_output" != *"Is the docker daemon running"* ]]; then
    return
  fi

  require_passwordless_sudo

  if start_docker_with_systemctl; then
    return
  fi

  if start_docker_with_service; then
    return
  fi

  if [[ "$DOCKER_INSTALLED" -eq 1 ]]; then
    fail "Docker packages were installed, but no supported service manager was found to start Docker."
  fi

  fail "Docker is installed but the daemon is stopped, and no supported service manager was found to start it. Start Docker before rerunning bootstrap."
}

install_docker_if_needed() {
  local -a packages=()

  if have_command docker && docker buildx version >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    return
  fi

  ensure_docker_repo

  if ! have_command docker; then
    packages+=(docker-ce docker-ce-cli containerd.io)
  fi
  if ! docker buildx version >/dev/null 2>&1; then
    packages+=(docker-buildx-plugin)
  fi
  if ! docker compose version >/dev/null 2>&1; then
    packages+=(docker-compose-plugin)
  fi

  if [[ "${#packages[@]}" -gt 0 ]]; then
    install_packages "${packages[@]}"
    if [[ " ${packages[*]} " == *" docker-ce "* || " ${packages[*]} " == *" containerd.io "* ]]; then
      DOCKER_INSTALLED=1
    fi
  fi
}

verify_required_commands() {
  have_command git || fail "git is required but unavailable. Jenkins checked out SCM before bootstrap, so install git on the runner image."
  have_command python3 || fail "python3 is required but unavailable."
  python3 -m pip --version >/dev/null 2>&1 || fail "python3 pip support is required. Install python3-pip."
  python3 -m venv --help >/dev/null 2>&1 || fail "python3 venv support is required. Install python3-venv."
  have_command node || fail "node is required but unavailable."
  have_command npm || fail "npm is required but unavailable."
  have_command rg || fail "rg (ripgrep) is required but unavailable."
  have_command docker || fail "docker is required but unavailable."
  docker buildx version >/dev/null 2>&1 || fail "docker buildx is required but unavailable. Install docker-buildx-plugin."
  docker compose version >/dev/null 2>&1 || fail "docker compose is required but unavailable. Install docker-compose-plugin."
}

verify_docker_access() {
  if docker info >/dev/null 2>&1; then
    return
  fi

  fail "Docker is installed but user '$(current_user)' cannot access the daemon. Add the user to the docker group or run Jenkins with Docker socket access, then retry."
}

ensure_builder_exists() {
  if docker buildx inspect "$BUILDER" >/dev/null 2>&1; then
    return
  fi

  log "Creating buildx builder: $BUILDER"
  docker buildx create --name "$BUILDER" --driver docker-container >/dev/null
}

builder_supports_required_platforms() {
  local inspect_output="$1"

  [[ "$inspect_output" == *"linux/arm64"* && "$inspect_output" == *"linux/arm/v7"* ]]
}

ensure_binfmt_support() {
  local inspect_output

  inspect_output="$(docker buildx inspect "$BUILDER" 2>/dev/null || true)"
  if builder_supports_required_platforms "$inspect_output"; then
    return
  fi

  log "Installing binfmt handlers for multi-arch builds"
  docker run --privileged --rm tonistiigi/binfmt --install all >/dev/null
}

bootstrap_builder() {
  local inspect_output

  inspect_output="$(docker buildx inspect --bootstrap "$BUILDER")"
  builder_supports_required_platforms "$inspect_output" || fail "Buildx builder '$BUILDER' is missing linux/arm64 or linux/arm/v7 support after bootstrap. Confirm Docker can run privileged containers and retry."
  log "Builder ready: $BUILDER"
}

warn() {
  printf '[bootstrap] WARN: %s\n' "$*" >&2
}

setup_warp_if_needed() {
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if [[ -x "${script_dir}/setup_jenkins_warp.sh" ]]; then
    log "running setup_jenkins_warp.sh"
    "${script_dir}/setup_jenkins_warp.sh"
  else
    warn "setup_jenkins_warp.sh missing or not executable; skipping WARP setup"
  fi
}

print_versions() {
  log "git --version"
  git --version

  log "python3"
  python3 --version

  log "python3 -m pip --version"
  python3 -m pip --version

  log "python3 -m venv --help"
  python3 -m venv --help >/dev/null
  printf 'python3 -m venv --help: ok\n'

  log "rg --version"
  rg --version

  log "node --version"
  node --version

  log "npm --version"
  npm --version

  log "docker version"
  docker version

  log "docker buildx version"
  docker buildx version

  log "docker compose version"
  docker compose version
}

main() {
  ensure_linux
  load_os_release

  install_base_dependencies
  install_node_if_needed
  install_docker_if_needed
  ensure_docker_service
  setup_warp_if_needed

  verify_required_commands
  verify_docker_access
  ensure_builder_exists
  ensure_binfmt_support
  bootstrap_builder
  print_versions
}

main "$@"
