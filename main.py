from agentic_workflow import run_agentic_workflow
import os
from emailPackage import send_G_Email


def main():
    try:
        repo_url = os.getenv("GITHUB_REPO_URL_PUBLIC")
        github_token = os.getenv("GITHUB_TOKEN")
        if not repo_url:
            repo_url = input("Enter the GitHub repository URL: ")
        
        if not github_token:
            raise ValueError("GitHub token not found in environment variables")
    
        result = run_agentic_workflow(repo_url)
        print(f"Analysis saved to: {result['pdf_path']}")

        if result :
            print(f"Analysis saved to: {result['pdf_path']}")

            #SEND MAIL
            sender=os.getenv("SENDER_EMAIL")
            reciever=os.getenv("RECIEVER_EMAIL")
            cc=os.getenv("CC")
            filePath=result['pdf_path']
            appendMessage="""
            ------------------------
            Any new line to be added
            """
            success = False
            
            try:
                # success = send_G_Email(sender,reciever,cc,filePath,appendMessage)
                # success = send_O_Email(sender, reciever, cc, filePath, appendMessage)
                if success:
                    print("EMAIL SENT")
                elif not success:
                    print("Failed to send email")
            except Exception as e:
                print(f"Error: {str(e)}")

        else:
            print("Analysis failed - check repository access")
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
