import os
import random
import datetime
import subprocess
import json
import time
import shutil

CONFIG_FILE = "config.json"
HISTORY_FILE = "history.json"
LOG_FILE = "ghost_log.txt"

def log_activity(message):
    """Appends a message to the log file with a timestamp."""
    utc_now = datetime.datetime.utcnow()
    ist_now = utc_now + datetime.timedelta(hours=5, minutes=30)
    timestamp = ist_now.strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {message}\n"
    
    print(log_entry.strip())
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Failed to write logs: {e}")

def push_logs(token=None):
    """Pushes the log file to the repo."""
    try:
        # If we are in the main repo context (not temp), git commands works directly
        if os.path.exists(".git"):
            subprocess.run("git config user.name 'Ghost Agent'", shell=True)
            subprocess.run("git config user.email 'agent@ghost.local'", shell=True)
            subprocess.run(f"git add {LOG_FILE}", shell=True)
            subprocess.run(f"git commit -m 'chore: update logs'", shell=True)
            # Just push using the current auth (GITHUB_TOKEN from checkout)
            subprocess.run("git push", shell=True)
    except Exception as e:
        print(f"Failed to push logs: {e}")

def load_json(filepath):
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def load_config():
    return load_json(CONFIG_FILE)


def run_command(command, cwd=None):
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
            shell=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Stderr: {e.stderr}")
        return None

def get_current_hour():
    # Force IST (India Standard Time) = UTC + 5:30
    # GitHub Actions runs on UTC, so we must adjust manually
    utc_now = datetime.datetime.utcnow()
    ist_now = utc_now + datetime.timedelta(hours=5, minutes=30)
    hour = ist_now.hour
    
    # Debug print to verify time in logs
    print(f"Current Time (IST): {ist_now.strftime('%Y-%m-%d %H:%M:%S')} | Hour: {hour}")
    
    if hour < 4: 
        hour += 24
    return hour

def should_run(schedule):
    current_h = get_current_hour()
    for block in schedule['blocks']:
        if block['start'] <= current_h <= block['end']:
            roll = random.random()
            print(f"Time {current_h}:00 matches block '{block['desc']}'. Roll: {roll:.2f} vs Prob: {block['probability']}")
            if roll < block['probability']:
                return True
    print(f"No active block for hour {current_h}:00 (or roll failed).")
    return False

def setup_repo(repo_url, token):
    """Clones a remote repo to a temp directory using the token."""
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    temp_dir = f"temp_{repo_name}_{int(time.time())}"
    
    # Insert token into URL for auth
    # Format: https://TOKEN@github.com/user/repo.git
    if "https://" in repo_url:
        auth_url = repo_url.replace("https://", f"https://{token}@")
    else:
        auth_url = repo_url # Assume user might have provided full auth url (unlikely)

    print(f"Cloning {repo_name}...")
    run_command(f"git clone {auth_url} {temp_dir}")
    
    if os.path.exists(temp_dir):
        # Configure git in the temp repo
        run_command("git config user.name 'Ghost Agent'", cwd=temp_dir)
        run_command("git config user.email 'agent@ghost.local'", cwd=temp_dir)
        return temp_dir
    return None

def cleanup_repo(temp_dir):
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        print(f"Cleaned up {temp_dir}")

def find_target_files(repo_path, config):
    targets = []
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in config['ignore_dirs']]
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in config['extensions']:
                targets.append(os.path.join(root, file))
    return targets

def get_comment_syntax(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.py', '.rb', '.sh', '.bash', '.zsh', '.pl']:
        return "# "
    elif ext in ['.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.cs', '.go', '.rs', '.kt', '.kts', '.swift', '.dart', '.php', '.groovy', '.vue', '.svelte']:
        return "// "
    elif ext in ['.lua']:
        return "-- "
    return None

def undo_last_change(history, repo_path):
    """Attempts to remove the last bot comment using history tracking."""
    if not history:
        return False

    # The file path in history is relative to the repo root. 
    # We need to join it with the current temp repo path.
    rel_path = history.get('rel_path')
    expected_content = history.get('added_content')
    
    if not rel_path:
        return False
        
    file_path = os.path.join(repo_path, rel_path)
    
    if not os.path.exists(file_path):
        print("File from history not found in current repo.")
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            return False

        last_line = lines[-1]
        
        if last_line.strip() == expected_content.strip():
            lines = lines[:-1]
            if lines and lines[-1].strip() == "":
                lines = lines[:-1]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"Undid changes in {rel_path}")
            return True
        else:
            print(f"File modified by user. Skipping undo.")
            return False
            
    except Exception as e:
        print(f"Error undoing change: {e}")
        return False

def apply_new_change(repo_path, config):
    candidates = find_target_files(repo_path, config)
    if not candidates:
        return None

    target_file = random.choice(candidates)
    syntax = get_comment_syntax(target_file)
    
    if not syntax:
        return None

    try:
        with open(target_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        comment_msg = random.choice(config['comments'])
        
        prefix = "\n"
        if lines and not lines[-1].endswith("\n"):
            prefix = "\n"
        elif not lines:
            prefix = ""
        if lines and lines[-1].strip() != "":
            prefix = "\n\n"

        full_comment_str = f"{prefix}{syntax}{comment_msg}\n"
        
        lines.append(full_comment_str)
        
        with open(target_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
            
        print(f"Added comment to {os.path.basename(target_file)}")
        
        return {
            "rel_path": os.path.relpath(target_file, repo_path),
            "added_content": f"{syntax}{comment_msg}",
            "timestamp": time.time()
        }
        
    except Exception as e:
        print(f"Error modifying {target_file}: {e}")
        return None

def main():
    log_activity("--- Cloud Agent Started ---")
    
    try:
        config = load_config()
        log_activity("Config loaded")
    except Exception as e:
        log_activity(f"Failed to load config: {e}")
        push_logs()
        return

    history = load_json(HISTORY_FILE)
    
    token = os.environ.get("GH_PAT")
    if not token:
        log_activity("Error: GH_PAT environment variable not found.")
        push_logs()
        return

    if not should_run(config['schedule']):
        log_activity("Schedule check: SKIP")
        push_logs(token)
        return

    log_activity("Schedule check: RUN - Proceeding with execution")

    # Decide how many commits to make this session (1-23 range)
    # More commits during main shift, fewer during secondary
    current_h = get_current_hour()
    if 9 <= current_h <= 27:  # Full day coverage (Max Power)
        num_commits = random.randint(5, 15)  # HEAVY load: 5 to 15 commits per session
    else:
        num_commits = random.randint(1, 3)
    
    log_activity(f"Planning to make {num_commits} commit(s) this session (Hour: {current_h})")
    
    commits_made = 0
    
    # Try to undo history if it exists (counts as 1 commit)
    if history and random.random() < 0.3:  # Reduced probability to allow more new commits
        target_repo_url = history.get('repo_url')
        if target_repo_url:
            print(f"Attempting cleanup on {target_repo_url}")
            temp_repo = setup_repo(target_repo_url, token)
            if temp_repo:
                if undo_last_change(history, temp_repo):
                    run_command("git add .", cwd=temp_repo)
                    run_command('git commit -m "refactor: cleanup"', cwd=temp_repo)
                    run_command("git push", cwd=temp_repo)
                    save_json(HISTORY_FILE, {})
                    commits_made += 1
                    log_activity(f"Cleanup commit made ({commits_made}/{num_commits})")
                cleanup_repo(temp_repo)
            else:
                 log_activity(f"Failed to setup repo for cleanup: {target_repo_url}")

    # Make remaining commits
    while commits_made < num_commits:
        repo_urls = config['repos']
        if not repo_urls:
            log_activity("No repos configured.")
            break

        target_url = random.choice(repo_urls)
        temp_repo = setup_repo(target_url, token)
        
        if temp_repo:
            new_history_data = apply_new_change(temp_repo, config)
            if new_history_data:
                # Only save the LAST commit to history for cleanup next time
                if commits_made == num_commits - 1:
                    new_history_data['repo_url'] = target_url
                    save_json(HISTORY_FILE, new_history_data)
                
                message = random.choice(config['commit_messages'])
                run_command("git add .", cwd=temp_repo)
                run_command(f'git commit -m "{message}"', cwd=temp_repo)
                run_command("git push", cwd=temp_repo)
                commits_made += 1
                log_activity(f"Commit made to {target_url.split('/')[-1]} ({commits_made}/{num_commits})")
            else:
                 log_activity(f"Failed to apply new change/modify file in {target_repo}")
            
            cleanup_repo(temp_repo)
        else:
            log_activity(f"Failed to setup repo: {target_url}")
        
        # Small delay between commits to look more human
        if commits_made < num_commits:
            time.sleep(random.randint(2, 8))
    
    log_activity(f"Session complete! Made {commits_made} commit(s)")
    push_logs(token)

if __name__ == "__main__":
    main()

