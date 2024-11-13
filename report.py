import requests
import argparse
from collections import defaultdict
from datetime import datetime

def run_query(query, variables, token):
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json={'query': query, 'variables': variables}, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed with status code {response.status_code}: {response.text}")

def get_prs(org, username, token):
    query = f'''
    query ($cursor: String) {{
      search(query: "is:pr author:{username} org:{org}", type: ISSUE, first: 100, after: $cursor) {{
        edges {{
          node {{
            ... on PullRequest {{
              title
              url
              createdAt
              mergedAt
              repository {{
                nameWithOwner
              }}
              commits {{
                totalCount
              }}
              additions
              deletions
              comments {{
                totalCount
              }}
            }}
          }}
        }}
        pageInfo {{
          hasNextPage
          endCursor
        }}
      }}
    }}
    '''
    
    pr_data = []
    monthly_summary = defaultdict(lambda: {
        'total_prs': 0,
        'total_commits': 0,
        'total_comments': 0,
        'total_additions': 0,
        'total_deletions': 0,
        'total_changes': 0,
    })
    
    cursor = None
    
    while True:
        variables = {
            "cursor": cursor
        }
        
        result = run_query(query, variables, token)
        
        pull_requests = result.get('data', {}).get('search', {}).get('edges', [])
        
        for pr in pull_requests:
            pr_node = pr['node']
            pr_info = {
                'title': pr_node['title'],
                'url': pr_node['url'],
                'createdAt': pr_node['createdAt'],
                'mergedAt': pr_node['mergedAt'],
                'repository': pr_node['repository']['nameWithOwner'],
                'commits_count': pr_node['commits']['totalCount'],
                'additions': pr_node['additions'],
                'deletions': pr_node['deletions'],
                'comments_count': pr_node['comments']['totalCount']
            }
            pr_data.append(pr_info)

            # 按合并时间统计
            if pr_node['mergedAt']:  # 只在 PR 已合并的情况下处理统计
                merged_month = datetime.fromisoformat(pr_node['mergedAt'][:-1]).strftime('%Y-%m')
                
                # 更新月份统计
                monthly_summary[merged_month]['total_prs'] += 1
                monthly_summary[merged_month]['total_commits'] += pr_node['commits']['totalCount']
                monthly_summary[merged_month]['total_comments'] += pr_node['comments']['totalCount']
                monthly_summary[merged_month]['total_additions'] += pr_node['additions']
                monthly_summary[merged_month]['total_deletions'] += pr_node['deletions']
                monthly_summary[merged_month]['total_changes'] += (pr_node['additions'] + pr_node['deletions'])
        
        page_info = result.get('data', {}).get('search', {}).get('pageInfo', {})
        if not page_info.get('hasNextPage'):
            break
        cursor = page_info['endCursor']
    
    return pr_data, monthly_summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub Pull Request - 统计与综述")
    parser.add_argument("token", help="GitHub Access Token")
    parser.add_argument("username", help="要查询的用户名")
    parser.add_argument("org", help="要查询的组织名")
    
    args = parser.parse_args()
    
    try:
        pr_data, monthly_summary = get_prs(args.org, args.username, args.token)
        
        # 输出以 PR 为单位的信息
        output = "# PR 详细信息\n\n"
        for pr in pr_data:
            output += f"## {pr['title']} (在 {pr['repository']} 中)\n"
            output += f"- [查看 PR]({pr['url']})\n"
            output += f"- 创建时间: {pr['createdAt']}\n"
            output += f"- 合并时间: {pr['mergedAt'] or '未合并'}\n"
            output += f"- 提交数量: {pr['commits_count']}\n"
            output += f"- 新增行数: {pr['additions']}\n"
            output += f"- 删除行数: {pr['deletions']}\n"
            output += f"- 评论数量: {pr['comments_count']}\n"
            output += "\n"
        
        # 输出按月统计的信息
        output += "# 月度综述\n\n"
        for month, summary in sorted(monthly_summary.items()):
            output += f"## {month}\n"
            output += f"- 总 PR 数: {summary['total_prs']}\n"
            output += f"- 提交总数: {summary['total_commits']}\n"
            output += f"- 评论总数: {summary['total_comments']}\n"
            output += f"- 新增行数: {summary['total_additions']}\n"
            output += f"- 删除行数: {summary['total_deletions']}\n"
            output += f"- 变动行数: {summary['total_changes']}\n"
            output += "\n"
        
        # 输出最终统计概述
        total_stats = {
            'total_prs': len(pr_data),
            'total_commits': sum(pr['commits_count'] for pr in pr_data),
            'total_comments': sum(pr['comments_count'] for pr in pr_data),
            'total_additions': sum(pr['additions'] for pr in pr_data),
            'total_deletions': sum(pr['deletions'] for pr in pr_data),
            'total_changes': sum(pr['additions'] + pr['deletions'] for pr in pr_data),
        }
        
        output += "# 总体统计\n\n"
        output += f"- 总 PR 数: {total_stats['total_prs']}\n"
        output += f"- 提交总数: {total_stats['total_commits']}\n"
        output += f"- 评论总数: {total_stats['total_comments']}\n"
        output += f"- 新增行数: {total_stats['total_additions']}\n"
        output += f"- 删除行数: {total_stats['total_deletions']}\n"
        output += f"- 变动行数: {total_stats['total_changes']}\n"

        print(output)

    except Exception as e:
        print(e)