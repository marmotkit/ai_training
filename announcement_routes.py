"""
公告管理相關路由和功能
"""

from flask import request, jsonify
from datetime import datetime
import os

def register_announcement_routes(app, login_required, load_data_from_file, save_data_to_file, ANNOUNCEMENTS_FILE):
    """註冊公告管理相關的路由"""
    
    # 添加公告
    @app.route('/lecturer/add-announcement', methods=['POST'])
    @login_required
    def add_announcement():
        try:
            # 獲取表單數據
            title = request.form.get('title')
            content = request.form.get('content')
            important = request.form.get('important', 'false') == 'true'
            
            # 驗證數據
            if not title or not content:
                return jsonify({'success': False, 'message': '標題和內容不能為空'}), 400
            
            # 獲取當前日期
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # 加載現有公告
            announcements = load_data_from_file(ANNOUNCEMENTS_FILE, [])
            
            # 生成新ID
            new_id = 1
            if announcements:
                new_id = max(announcement.get('id', 0) for announcement in announcements) + 1
            
            # 創建新公告
            new_announcement = {
                'id': new_id,
                'title': title,
                'content': content,
                'date': current_date,
                'important': important
            }
            
            # 添加到列表
            announcements.append(new_announcement)
            
            # 保存到文件
            if save_data_to_file(ANNOUNCEMENTS_FILE, announcements):
                return jsonify({'success': True, 'message': '公告添加成功', 'announcement': new_announcement})
            else:
                return jsonify({'success': False, 'message': '保存公告時發生錯誤'}), 500
                
        except Exception as e:
            return jsonify({'success': False, 'message': f'添加公告時發生錯誤: {str(e)}'}), 500

    # 編輯公告
    @app.route('/lecturer/edit-announcement', methods=['POST'])
    @login_required
    def edit_announcement():
        try:
            # 獲取表單數據
            announcement_id = int(request.form.get('id'))
            title = request.form.get('title')
            content = request.form.get('content')
            important = request.form.get('important', 'false') == 'true'
            
            # 驗證數據
            if not title or not content:
                return jsonify({'success': False, 'message': '標題和內容不能為空'}), 400
            
            # 加載現有公告
            announcements = load_data_from_file(ANNOUNCEMENTS_FILE, [])
            
            # 查找要編輯的公告
            announcement_found = False
            for announcement in announcements:
                if announcement.get('id') == announcement_id:
                    announcement['title'] = title
                    announcement['content'] = content
                    announcement['important'] = important
                    announcement_found = True
                    break
            
            if not announcement_found:
                return jsonify({'success': False, 'message': '找不到指定的公告'}), 404
            
            # 保存到文件
            if save_data_to_file(ANNOUNCEMENTS_FILE, announcements):
                return jsonify({'success': True, 'message': '公告更新成功'})
            else:
                return jsonify({'success': False, 'message': '保存公告時發生錯誤'}), 500
                
        except Exception as e:
            return jsonify({'success': False, 'message': f'編輯公告時發生錯誤: {str(e)}'}), 500

    # 刪除公告
    @app.route('/lecturer/delete-announcement', methods=['POST'])
    @login_required
    def delete_announcement():
        try:
            # 獲取公告ID
            announcement_id = int(request.form.get('id'))
            
            # 加載現有公告
            announcements = load_data_from_file(ANNOUNCEMENTS_FILE, [])
            
            # 過濾掉要刪除的公告
            filtered_announcements = [a for a in announcements if a.get('id') != announcement_id]
            
            # 檢查是否找到並刪除了公告
            if len(filtered_announcements) == len(announcements):
                return jsonify({'success': False, 'message': '找不到指定的公告'}), 404
            
            # 保存到文件
            if save_data_to_file(ANNOUNCEMENTS_FILE, filtered_announcements):
                return jsonify({'success': True, 'message': '公告刪除成功'})
            else:
                return jsonify({'success': False, 'message': '保存公告時發生錯誤'}), 500
                
        except Exception as e:
            return jsonify({'success': False, 'message': f'刪除公告時發生錯誤: {str(e)}'}), 500
